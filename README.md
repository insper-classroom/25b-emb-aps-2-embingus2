# Controle Glock para Counter-Strike 2 - APS-2

Este repositório contém o projeto de um controle customizado para o jogo Counter-Strike 2, desenvolvido como parte da disciplina de Computação Embarcada (APS-2). O controle tem o formato de uma pistola Glock e foi projetado para substituir o mouse, permitindo que o jogador utilize a mão direita para mira e ações, enquanto a mão esquerda permanece no teclado para movimentação.

## 🎥 Vídeo de Demonstração

Confira o controle em ação no vídeo abaixo:

**[Controle Glock para CS2 - Demonstração](https://youtu.be/_YVrig4paHU)**

[![Demonstração do Controle](https://img.youtube.com/vi/_YVrig4paHU/0.jpg)](https://youtu.be/_YVrig4paHU)

## 🎮 O Jogo

O controle foi projetado especificamente para **Counter-Strike 2**, um jogo de tiro tático em primeira pessoa que exige precisão e tempo de resposta baixos.

- **Link do Jogo:** [Counter-Strike 2 na Steam](https://store.steampowered.com/app/730/CounterStrike_2/)

## 💡 Ideia do Controle

A principal motivação é criar uma experiência de jogo mais imersiva e intuitiva. Em vez de mover um mouse sobre uma mesa, o jogador aponta o controle-pistola para controlar a mira.

Para permitir o reposicionamento da mira sem afetar o jogo, o equivalente a levantar um mouse do mousepad, foi implementado um **botão de "clutch" (ou "freeze")**. Ao segurá-lo, o movimento da IMU é ignorado, permitindo que o jogador retorne o controle a uma posição central e confortável sem mover a câmera do personagem.

## ⚙️ Inputs e Outputs (Hardware)

O controle utiliza os seguintes componentes:

### Entradas (Sensores)

- **IMU (HW-290):** Um giroscópio que captura a velocidade de rotação do controle para controlar a mira do mouse.
- **Botão 1 (Gatilho):** `BTN_GATILHO_PIN` (GP17) - Ação de atirar (clique esquerdo do mouse).
- **Botão 2 (Mira):** `BTN_MIRA_PIN` (GP16) - Ação de mirar (clique direito do mouse).
- **Botão 3 (Arma Próxima):** `BTN_PROX_PIN` (GP28) - Roda do mouse para cima.
- **Botão 4 (Reposicionamento):** `BTN_MOUSE_PULL` (GP27) - Botão "clutch" que desativa temporariamente o envio de dados da IMU.

### Saídas (Atuadores)

- **LED de Status:** `LED_STATUS_PIN` (GP25) - Um LED que acende para indicar que o firmware está rodando e o controle está pronto para uso.

## 📡 Protocolo Utilizado

A comunicação com o computador é feita via **UART (Serial)** através do cabo USB. Um script em Python rodando no PC lê os dados da porta serial e os traduz em comandos de mouse.

Foi definido um protocolo de texto simples e customizado:

- **Movimento:** `M,<delta_x>,<delta_y>\n`
  - Ex: `M,-15,5\n`
- **Botão Pressionado:** `BD,<id_botao>\n`
  - Ex: `BD,1\n` (Gatilho pressionado)
- **Botão Solto:** `BU,<id_botao>\n`
  - Ex: `BU,1\n` (Gatilho solto)

## 📊 Diagrama de Blocos do Firmware

A arquitetura do firmware é baseada em um **RTOS (Real-Time Operating System)** para gerenciar as múltiplas tarefas de forma concorrente e organizada.

O diagrama de blocos a seguir detalha a arquitetura do firmware e **foi validado pelo Prof. Corsi**.

![Diagrama do Firmware](diagrama.png)

### Explicação dos Componentes do Diagrama

- **Tasks (Tarefas):**
  - `imu_task`: Tarefa dedicada a ler os dados do giroscópio em alta frequência, calibrá-los e enviá-los ao PC via UART.
  - `btn_task`: Tarefa que aguarda eventos de botões (colocados em uma fila pela ISR) e envia o estado (`Pressionado` ou `Solto`) ao PC.
  - `status_task`: Tarefa de baixa prioridade que acende o LED de status para indicar que o sistema foi inicializado corretamente.

- **ISRs (Interrupt Service Routines):**
  - `btn_callback`: Uma rotina de interrupção que é ativada por qualquer um dos cinco botões. Sua função é registrar o pino e o estado (pressionado/solto) e enviar essa informação para a `qButtonEvents`, mantendo a interrupção o mais rápida possível.

- **Queues (Filas):**
  - `qButtonEvents`: Fila utilizada para desacoplar a ISR dos botões da `btn_task`.

- **Semáforos / Mutexes (Consideração de Implementação):**
  - Um **mutex** (`uart_mutex`) é utilizado para proteger o acesso à UART. Como tanto a `imu_task` quanto a `btn_task` enviam dados, o mutex garante que as mensagens não se misturem, evitando corrupção do protocolo.

## ✅ Qualidade de Código

O código-fonte deste projeto segue as boas práticas de desenvolvimento para sistemas embarcados e foi validado com as ferramentas `cppcheck` e `embedded-check` para garantir a ausência de erros comuns e a conformidade com os padrões de qualidade.
