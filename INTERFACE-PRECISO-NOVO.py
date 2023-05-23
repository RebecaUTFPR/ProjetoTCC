import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog

# Variáveis de calibração
calibrando = True
pontos_calibracao = []
distancia_calibracao_cm = 0
escala_conversao = 0

# Variáveis para cálculo de velocidade
velocidade_maxima = 0
velocidade_maxima_torricelli = 0
tempos = []
aceleracoes = []
posicao_anterior = None
posicao_inicial = None
tempo_anterior = cv2.getTickCount() / cv2.getTickFrequency()

# Variável para rastrear se estamos no primeiro frame
primeiro_frame = True


def escolher_arquivo():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path


def digitar_tamanho():
    root = tk.Tk()
    root.withdraw()

    # Variável distancia inserida pelo usuario
    distancia = tk.DoubleVar()

    # Função que será chamada quando o usuário clicar no botão "OK"
    def on_ok():
        # Ler entrada do usuario na distancia
        distancia.set(entrada.get())
        # Fechar após o usuário clicar em "OK"
        janela_calibracao.destroy()

    janela_calibracao = tk.Toplevel(root)
    janela_calibracao.title("Distância de Calibração")
    tk.Label(janela_calibracao, text="Informe a distância real entre os pontos (em centímetros): ").pack()
    entrada = tk.Entry(janela_calibracao)
    entrada.pack()
    tk.Button(janela_calibracao, text="OK", command=on_ok).pack()
    root.wait_window(janela_calibracao)

    return distancia.get()


def clicar_calibracao(event, x, y, flags, param):
    global calibrando, pontos_calibracao, distancia_calibracao_cm, escala_conversao

    if event == cv2.EVENT_LBUTTONDOWN:
        if calibrando:
            pontos_calibracao.append((x, y))
            if len(pontos_calibracao) == 2:
                distancia_pixels = np.linalg.norm(np.array(pontos_calibracao[0]) - np.array(pontos_calibracao[1]))
                distancia_calibracao_cm = digitar_tamanho()
                escala_conversao = distancia_calibracao_cm / distancia_pixels

                print("Calibração concluída!")
                print(f"Escala de conversão: 1 pixel = {escala_conversao:.2f} cm")

                calibrando = False


# Função para encontrar o contorno do amarelo do martelo
def encontrar_contorno_amarelo(imagem):
    hsv = cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV)
    limite_inferior = np.array([20, 100, 100])
    limite_superior = np.array([30, 255, 255])
    mascara = cv2.inRange(hsv, limite_inferior, limite_superior)
    kernel = np.ones((5, 5), np.uint8)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contornos


# Função para desenhar contornos na imagem original
def desenhar_contornos(imagem, contornos):
    for contorno in contornos:
        x, y, w, h = cv2.boundingRect(contorno)
        cv2.rectangle(imagem, (x, y), (x + w, y + h), (0, 255, 0), 2)


# Função para desenhar pontos de calibração
def desenhar_pontos_calibracao(imagem, pontos):
    for ponto in pontos:
        cv2.circle(imagem, ponto, 5, (0, 0, 255), -1)


# Caminho para o arquivo de vídeo
video_path = escolher_arquivo()

# Inicializar a leitura do vídeo
captura = cv2.VideoCapture(video_path)
altura_original = int(captura.get(cv2.CAP_PROP_FRAME_HEIGHT))
nova_largura = 800
nova_altura = int(altura_original * nova_largura / nova_largura)



while True:
    ret, frame = captura.read()
    if not ret:
        break

    frame = cv2.resize(frame, (nova_largura, nova_altura))

    # Desenhar os pontos de calibração
    desenhar_pontos_calibracao(frame, pontos_calibracao)

    if calibrando:
        cv2.putText(frame, "Clique em dois pontos para calibrar", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0),
                    2)

        # Mostrar o quadro e configurar o callback do mouse
        cv2.imshow("Detectando a queda do martelo", frame)
        cv2.setMouseCallback("Detectando a queda do martelo", clicar_calibracao)

        # Se estivermos no primeiro frame, aguardar até que a calibração seja concluída
        if primeiro_frame:
            while calibrando:
                cv2.waitKey(1)
            # Definir primeiro_frame para False depois que a calibração for concluída
            primeiro_frame = False

        # Se o loop while foi interrompido porque a calibração terminou, continue para o próximo quadro
        if not calibrando:
            continue
    else:
        contornos_amarelos = encontrar_contorno_amarelo(frame)
        desenhar_contornos(frame, contornos_amarelos)

        if len(contornos_amarelos) > 0:
            contorno = max(contornos_amarelos, key=cv2.contourArea)
            momento = cv2.moments(contorno)
            centro_x = int(momento["m10"] / momento["m00"])
            centro_y = int(momento["m01"] / momento["m00"])

            if posicao_anterior is None:
                posicao_anterior = centro_y
                posicao_inicial = centro_y
                continue

            posicao_atual = centro_y
            altura_metros = abs(posicao_inicial - posicao_atual) * escala_conversao / 100  # altura em metros
            posicao_anterior = posicao_atual

            tempo_atual = cv2.getTickCount() / cv2.getTickFrequency()
            tempo_decorrido = tempo_atual - tempo_anterior
            tempo_anterior = tempo_atual

            #Aplico a forma de torricelli para o calculo da velocidade
            velocidade_torricelli = np.sqrt(2 * 9.64 * altura_metros)
            aceleracao = (velocidade_torricelli - velocidade_maxima_torricelli) / tempo_decorrido

            if velocidade_torricelli > velocidade_maxima_torricelli:
                velocidade_maxima_torricelli = velocidade_torricelli

            texto_velocidade_torricelli = f"Velocidade de queda por Torricelli: {velocidade_torricelli:.2f} m/s"
            texto_velocidade_maxima_torricelli = f"Velocidade máxima de queda por Torricelli: {velocidade_maxima_torricelli:.2f} m/s"
            cv2.putText(frame, texto_velocidade_torricelli, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, texto_velocidade_maxima_torricelli, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255),
                        2)

            tempos.append(tempo_atual)
            aceleracoes.append(aceleracao)

    cv2.imshow("Detectando a queda do martelo", frame)
    cv2.setMouseCallback("Detectando a queda do martelo", clicar_calibracao)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.waitKey(0)
captura.release()
cv2.destroyAllWindows()