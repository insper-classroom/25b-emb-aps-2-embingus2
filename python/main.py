import serial
import time
import pydirectinput
import pyautogui 

# --- CONFIGURAÇÕES ---
SERIAL_PORT = "COM5" 
BAUD_RATE = 115200

pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0.0

# ==========================================================
# MUDANÇA 1: Variável de estado global para o script Python
# ==========================================================
imu_active = True


def process_serial_data(line):
    """Interpreta uma linha de dados vinda da Pico e executa a ação correspondente."""
    
    # Precisamos informar à função que vamos MODIFICAR a variável global
    global imu_active 
    
    line = line.strip()
    parts = line.split(',')
    if not parts:
        return
        
    command = parts[0]
    
    try:
        # MUDANÇA 2: Lidar com "Botão Pressionado" (BD)
        if command == 'BD' and len(parts) == 2:
            button_id = int(parts[1])
            if button_id == 1: # Gatilho
                pydirectinput.mouseDown(button='left')
            elif button_id == 2: # Mira
                pydirectinput.mouseDown(button='right')
            elif button_id == 5: # <-- MUDANÇA 2.1: Detecta o botão de "levantar"
                imu_active = False # Desativa o movimento da IMU

        # MUDANÇA 3: Lidar com Movimento (M)
        elif command == 'M' and len(parts) == 3:
            # MUDANÇA 3.1: Só processa o movimento se a IMU estiver ativa
            if imu_active:
                dx = int(parts[1])
                dy = int(parts[2])
                pydirectinput.moveRel(dx, dy, relative=True)
                
        # MUDANÇA 4: Lidar com "Botão Solto" (BU)
        elif command == 'BU' and len(parts) == 2:
            button_id = int(parts[1])
            if button_id == 1: # Gatilho
                pydirectinput.mouseUp(button='left')
            elif button_id == 2: # Mira
                pydirectinput.mouseUp(button='right')
            elif button_id == 3: # Próxima arma
                pyautogui.scroll(120) 
            elif button_id == 4: # Arma anterior
                pyautogui.scroll(-1)
            elif button_id == 5: # <-- MUDANÇA 4.1: Detecta o soltar do botão
                imu_active = True # Reativa o movimento da IMU

    except (ValueError, IndexError) as e:
        print(f"Erro ao processar a linha '{line}': {e}")


def main():
    """Função principal: conecta à porta serial e entra no loop de leitura."""
    print("--- Glock Controller Interface ---")
    print(f"Tentando conectar a {SERIAL_PORT} a {BAUD_RATE} bps...")

    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("Conectado com sucesso! Lendo dados do controle...")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore')
                if line:
                    process_serial_data(line)
            time.sleep(0.001)

    except serial.SerialException as e:
        print(f"Erro: Não foi possível abrir a porta serial {SERIAL_PORT}.")
        print(f"Detalhes: {e}")
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Conexão serial fechada.")

if __name__ == "__main__":
    main()