import serial
import pyautogui
import time

# --- CONFIGURAÇÕES ---
# Altere para a porta serial correta da sua Pico.
# No Windows, é algo como "COM3". No Linux, "/dev/ttyACM0".
SERIAL_PORT = "COM5"
BAUD_RATE = 115200

# Desativa a trava de segurança do pyautogui que impede o mouse de ir para os cantos.
pyautogui.FAILSAFE = False
# Pequena pausa entre os comandos do pyautogui para não sobrecarregar
pyautogui.PAUSE = 0.0

def process_serial_data(line):
    """Interpreta uma linha de dados vinda da Pico e executa a ação correspondente."""
    
    # Remove espaços em branco e quebras de linha
    line = line.strip()
    
    # Separa o comando ('M' ou 'B') dos dados
    parts = line.split(',')
    if not parts:
        return
        
    command = parts[0]
    
    try:
        if command == 'M' and len(parts) == 3:
            # Comando de Movimento: M,dx,dy
            dx = int(parts[1])
            dy = int(parts[2])
            pyautogui.moveRel(dx, dy, duration=0.0) # duration=0.0 é o mais rápido
            
        elif command == 'B' and len(parts) == 2:
            # Comando de Botão: B,id_botao
            button_id = int(parts[1])
            if button_id == 1: # Gatilho
                pyautogui.click(button='left')
            elif button_id == 2: # Mira
                pyautogui.click(button='right')
            elif button_id == 3: # Próxima arma
                pyautogui.scroll(1) # Scroll para cima
            elif button_id == 4: # Arma anterior
                pyautogui.scroll(-1) # Scroll para baixo

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
            # Lê uma linha da porta serial (terminada em '\n')
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore')
                if line:
                    process_serial_data(line)
            # Uma pequena pausa para não sobrecarregar a CPU do PC
            time.sleep(0.001)

    except serial.SerialException as e:
        print(f"Erro: Não foi possível abrir a porta serial {SERIAL_PORT}.")
        print(f"Detalhes: {e}")
        print("Por favor, verifique se o dispositivo está conectado e a porta está correta.")
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Conexão serial fechada.")

if __name__ == "__main__":
    main()