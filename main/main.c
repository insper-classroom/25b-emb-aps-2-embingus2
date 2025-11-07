// main.c (CORRIGIDO PARA SPRAY E ESTADO)

#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/gpio.h"

#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"

/* ============== PIN DEFINITIONS ============== */
#define I2C_PORT i2c0
#define I2C_SDA_PIN 4
#define I2C_SCL_PIN 5

#define BTN_GATILHO_PIN 16
#define BTN_MIRA_PIN    11
#define BTN_PROX_PIN    12
#define BTN_ANT_PIN     13

#define LED_STATUS_PIN 25

/* ============== MPU6050 DEFINITIONS ============== */
#define MPU6050_ADDR         0x68
#define MPU6050_PWR_MGMT_1   0x6B
#define MPU6050_GYRO_XOUT_H  0x43
#define GYRO_DEADZONE        10.0f

/* ============== RTOS HANDLES ============== */
QueueHandle_t qButtonEvents;
SemaphoreHandle_t uart_mutex;

int32_t gyro_x_offset = 0;
int32_t gyro_y_offset = 0;

/* ============== STRUCTS ============== */
// MUDANÇA 1: Struct agora inclui o estado do botão (pressionado/solto)
typedef struct {
    uint8_t pin;
    uint8_t state; // 1 para PRESSIONADO (FALL), 0 para SOLTO (RISE)
} button_event_t;

/* ============== MPU6050 HELPER FUNCTIONS ============== */
void mpu6050_init() {
    uint8_t buf[] = {MPU6050_PWR_MGMT_1, 0x00};
    i2c_write_blocking(I2C_PORT, MPU6050_ADDR, buf, 2, false);
}

void mpu6050_read_gyro(int16_t gyro[3]) {
    uint8_t buffer[6];
    uint8_t reg = MPU6050_GYRO_XOUT_H;
    
    i2c_write_blocking(I2C_PORT, MPU6050_ADDR, &reg, 1, true);
    i2c_read_blocking(I2C_PORT, MPU6050_ADDR, buffer, 6, false);

    gyro[0] = (buffer[0] << 8) | buffer[1];
    gyro[1] = (buffer[2] << 8) | buffer[3];
    gyro[2] = (buffer[4] << 8) | buffer[5];
}


/* ============== ISR (CALLBACK) ============== */
// MUDANÇA 2: Callback agora envia o estado junto com o pino
void btn_callback(uint gpio, uint32_t events) {
    button_event_t event = {.pin = gpio};
    if ((events & GPIO_IRQ_EDGE_FALL) != 0) {
        event.state = 1; // Pressionado
        xQueueSendFromISR(qButtonEvents, &event, 0);
    } else if ((events & GPIO_IRQ_EDGE_RISE) != 0) {
        event.state = 0; // Solto
        xQueueSendFromISR(qButtonEvents, &event, 0);
    }
}


/* ============== TASKS ============== */

void imu_task(void *pvParameters) {
    i2c_init(I2C_PORT, 400 * 1000);
    gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA_PIN);
    gpio_pull_up(I2C_SCL_PIN);
    mpu6050_init();

    printf("Iniciando calibracao do IMU... Mantenha parado!\n");
    const int CALIBRATION_SAMPLES = 1000;
    gyro_x_offset = 0;
    gyro_y_offset = 0;
    int16_t gyro[3];

    for (int i = 0; i < CALIBRATION_SAMPLES; i++) {
        mpu6050_read_gyro(gyro);
        gyro_x_offset += gyro[0];
        gyro_y_offset += gyro[2]; // Usando Z para Yaw
        vTaskDelay(pdMS_TO_TICKS(2));
    }
    gyro_x_offset /= CALIBRATION_SAMPLES;
    gyro_y_offset /= CALIBRATION_SAMPLES;
    printf("Calibracao concluida. Offsets: X=%ld, Y=%ld\n", gyro_x_offset, gyro_y_offset);

    while (1) {
        mpu6050_read_gyro(gyro);
        int16_t corrected_gx = gyro[0] - (int16_t)gyro_x_offset;
        int16_t corrected_gy = gyro[2] - (int16_t)gyro_y_offset; // Usando Z para Yaw

        int16_t mouse_dx = -corrected_gy / 100;
        int16_t mouse_dy = -corrected_gx / 100;

        if (abs(corrected_gy) < GYRO_DEADZONE) mouse_dx = 0;
        if (abs(corrected_gx) < GYRO_DEADZONE) mouse_dy = 0;

        if (mouse_dx != 0 || mouse_dy != 0) {
            if (xSemaphoreTake(uart_mutex, portMAX_DELAY) == pdTRUE) {
                printf("M,%d,%d\n", mouse_dx, mouse_dy);
                xSemaphoreGive(uart_mutex);
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void btn_task(void *pvParameters) {
    uint8_t BTN_PINS[] = {BTN_GATILHO_PIN, BTN_MIRA_PIN, BTN_PROX_PIN, BTN_ANT_PIN};
    for (int i = 0; i < sizeof(BTN_PINS)/sizeof(BTN_PINS[0]); i++) {
        gpio_init(BTN_PINS[i]);
        gpio_set_dir(BTN_PINS[i], GPIO_IN);
        gpio_pull_up(BTN_PINS[i]);
        // MUDANÇA 3: Habilita interrupção para subida E descida
        gpio_set_irq_enabled_with_callback(BTN_PINS[i], GPIO_IRQ_EDGE_FALL | GPIO_IRQ_EDGE_RISE, true, &btn_callback);
    }

    button_event_t received_event;
    uint8_t button_id = 0;

    while (1) {
        if (xQueueReceive(qButtonEvents, &received_event, portMAX_DELAY) == pdPASS) {
            // REMOVIDO: Debounce com delay e reset de fila não funciona bem com estados
            switch (received_event.pin) {
                case BTN_GATILHO_PIN: button_id = 1; break;
                case BTN_MIRA_PIN:    button_id = 2; break;
                case BTN_PROX_PIN:    button_id = 3; break;
                case BTN_ANT_PIN:     button_id = 4; break;
                default:              button_id = 0; break;
            }

            if (button_id != 0) {
                if (xSemaphoreTake(uart_mutex, portMAX_DELAY) == pdTRUE) {
                    // MUDANÇA 4: Envia "BD" para Pressionado, "BU" para Solto
                    if (received_event.state == 1) { // Pressionado
                        printf("BD,%d\n", button_id);
                    } else { // Solto
                        printf("BU,%d\n", button_id);
                    }
                    xSemaphoreGive(uart_mutex);
                }
            }
        }
    }
}

void status_task(void *pvParameters) {
    gpio_init(LED_STATUS_PIN);
    gpio_set_dir(LED_STATUS_PIN, GPIO_OUT);
    gpio_put(LED_STATUS_PIN, 1);
    vTaskSuspend(NULL); 
}

int main(void) {
    stdio_init_all();
    qButtonEvents = xQueueCreate(10, sizeof(button_event_t));
    uart_mutex = xSemaphoreCreateMutex();
    xTaskCreate(imu_task, "IMUTask", 512, NULL, 1, NULL); // Aumentei um pouco o stack por causa da calibração
    xTaskCreate(btn_task, "ButtonTask", 256, NULL, 1, NULL);
    xTaskCreate(status_task, "StatusTask", 256, NULL, 1, NULL);
    vTaskStartScheduler();
    while (1);
}