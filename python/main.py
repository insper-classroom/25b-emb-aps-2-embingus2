import serial
import time
import pydirectinput # FIX 1: Importa a biblioteca correta

# Mantém o pyautogui para scroll, pois o pydirectinput não tem uma função de scroll fácil
import pyautogui 

# --- CONFIGURAÇÕES ---
SERIAL_PORT = "COM5" # Verifique se esta é a porta correta
BAUD_RATE = 115200

# FIX 2: Configurações para pydirectinput
pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0.0

def process_serial_data(line):
    """Interpreta uma linha de dados vinda da Pico e executa a ação correspondente."""
    line = line.strip()
    parts = line.split(',')
    if not parts:
        return
        
    command = parts[0]
    
    try:
        if command == 'M' and len(parts) == 3:
            # Comando de Movimento: M,dx,dy
            dx = int(parts[1])
            dy = int(parts[2])
            # FIX 3: Usa moveRel do pydirectinput
            pydirectinput.moveRel(dx, dy, relative=True)
            
        # MUDANÇA 5: Lida com eventos de "Botão Pressionado" (BD)
        elif command == 'BD' and len(parts) == 2:
            button_id = int(parts[1])
            if button_id == 1: # Gatilho
                pydirectinput.mouseDown(button='left')
            elif button_id == 2: # Mira
                pydirectinput.mouseDown(button='right')

        # MUDANÇA 6: Lida com eventos de "Botão Solto" (BU)
        elif command == 'BU' and len(parts) == 2:
            button_id = int(parts[1])
            if button_id == 1: # Gatilho
                pydirectinput.mouseUp(button='left')
            elif button_id == 2: # Mira
                pydirectinput.mouseUp(button='right')
            # Botões de scroll são eventos únicos, então tratamos no "soltar" para simular um clique
            elif button_id == 3: # Próxima arma
                pyautogui.scroll(1) 
            elif button_id == 4: # Arma anterior
                pyautogui.scroll(-1)

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