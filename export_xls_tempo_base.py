import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import time
import pandas as pd

# Variáveis de calibração
calibrando = True
pontos_calibracao = []
distancia_calibracao_cm = 0
escala_conversao = 0
ponto_inicio = None

# Variáveis para cálculo de velocidade
velocidade_maxima = 0
velocidade_maxima_torricelli = 0
tempos = []
aceleracoes = []
posicao_anterior = None
posicao_inicial = None
tempo_anterior = cv2.getTickCount() / cv2.getTickFrequency()
tempo_inicio_queda = None
ponto_inicial_queda = None
ponto_final_queda = None
ultima_centro_y = None
ponto_inferior_objeto = None
ponto_final_queda = None
ponto_inicial_queda = None
tempo_inicio_queda = None
tempo_final_queda = None

ponto_final = None
linha_final_definida = False

# Variável para rastrear se estamos no primeiro frame
primeiro_frame = True
valores = []

def adicionar_valor(distancia, tempo):
    valores.append([distancia, tempo])

def formatar_valor(distancia, tempo):
    distancia_formatada = f"{distancia:.2f} cm"
    tempo_formatado = f"{tempo:.2f} s"
    return distancia_formatada, tempo_formatado

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

def solicitar_ponto_inicio():
    root = tk.Tk()
    root.withdraw()

    janela_inicio = tk.Toplevel(root)
    janela_inicio.title("Ponto de início e final")
    tk.Label(janela_inicio, text="Clique na imagem para definir o ponto de início e, em seguida, o ponto final.").pack()
    tk.Button(janela_inicio, text="OK", command=janela_inicio.destroy).pack()
    root.wait_window(janela_inicio)

# Função para identificar se o objeto passou a linha amarela
def passou_linha_amarela(centro_y):
    global ponto_inicio, ponto_final

    if ponto_inicio is not None and ponto_final is not None:
        if ponto_inicio[1] < centro_y < ponto_final[1]:
            return True
    return False
# Função para identificar se o objeto passou a linha final
def passou_linha_final(centro_y):
    return ponto_final[1] < centro_y and ponto_final[1] > ponto_inicio[1]

def clicar_calibracao(event, x, y, flags, param):
    global calibrando, pontos_calibracao, distancia_calibracao_cm, escala_conversao, ponto_inicio, ponto_final, linha_final_definida

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
                solicitar_ponto_inicio()  # Solicitar ao usuário para definir o ponto de início e final
        elif ponto_inicio is None:
            ponto_inicio = (x, y)
            print("Linha inicial definida!")
        elif not linha_final_definida:
            ponto_final = (x, y)
            linha_final_definida = True
            print("Linha final definida!")


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
def desenhar_contorno(imagem, contornos):
    for contorno in contornos:
        x, y, w, h = cv2.boundingRect(contorno)
        ponto_inferior_objeto = y + h  # Ponto inferior do objeto
        cv2.rectangle(imagem, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.line(imagem, (x, ponto_inferior_objeto), (x + w, ponto_inferior_objeto), (255, 0, 255), 2)



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
        cv2.putText(frame, "Clique em dois pontos para calibrar", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    elif ponto_inicio is None:
        cv2.putText(frame, "Clique em um ponto para definir o ponto de início", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.line(frame, (0, ponto_inicio[1]), (nova_largura, ponto_inicio[1]), (0, 255, 255), 2)

    if linha_final_definida:
        cv2.line(frame, (0, ponto_final[1]), (nova_largura, ponto_final[1]), (0, 0, 255), 2)
    # Mostrar o quadro e configurar o callback do mouse
    cv2.imshow("Detectando a queda do martelo", frame)
    cv2.setMouseCallback("Detectando a queda do martelo", clicar_calibracao)
    # Se estivermos no primeiro frame, aguardar até que a calibração seja concluída
    if primeiro_frame:
        while calibrando or ponto_inicio is None:
            cv2.waitKey(1)
            # Definir primeiro_frame para False depois que a calibração for concluída
        primeiro_frame = False

        # Se o loop while foi interrompido porque a calibração terminou, continue para o próximo quadro
        if not calibrando:
            continue
    else:
        contornos_amarelos = encontrar_contorno_amarelo(frame)

        if len(contornos_amarelos) > 0:
            contorno = max(contornos_amarelos, key=cv2.contourArea)
            desenhar_contorno(frame, contornos_amarelos)
            momento = cv2.moments(contorno)
            centro_x = int(momento["m10"] / momento["m00"])
            centro_y = int(momento["m01"] / momento["m00"])
            x, y, w, h = cv2.boundingRect(contorno)
            ponto_inferior_objeto = y + h

            #Registra se o objeto cruzou a linha, para fins de validação
            if passou_linha_amarela(ponto_inferior_objeto) and tempo_inicio_queda is None:
                tempo_inicio_queda = cv2.getTickCount() / cv2.getTickFrequency()
                ponto_inicial_queda = ponto_inferior_objeto
                print("Objeto passou pela primeira linha")

            # Calcula a distância e tempo em cada frame depois de passar a linha amarela
            if tempo_inicio_queda is not None:
                tempo_atual = cv2.getTickCount() / cv2.getTickFrequency()
                tempo_desde_inicio_queda = tempo_atual - tempo_inicio_queda
                distancia_desde_inicio_queda_cm = abs(ponto_inferior_objeto - ponto_inicial_queda) * escala_conversao
                print(f"Distancia percorrida: {distancia_desde_inicio_queda_cm:.2f}cm, Tempo percorrido: {tempo_desde_inicio_queda:.2f} s")
                distancia_formatada, tempo_formatado = formatar_valor(distancia_desde_inicio_queda_cm, tempo_desde_inicio_queda)
                adicionar_valor(distancia_formatada, tempo_formatado)
               # print(f"Tempo desde a passagem pela linha amarela: {tempo_desde_inicio_queda:.2f} s")
               # print(f"Distância desde a passagem pela linha amarela: {distancia_desde_inicio_queda_cm:.2f} cm")

                
            #Aguarda queda finalizar, validando se o objeto ainda tá caindo
            if tempo_inicio_queda is not None and (ultima_centro_y is None or centro_y > ultima_centro_y):
                ponto_final_queda = centro_y

            if posicao_anterior is None:
                posicao_anterior = centro_y
                posicao_inicial = centro_y
                continue

            if ponto_final_queda is not None and (ultima_centro_y is not None and centro_y <= ultima_centro_y):
                tempo_final_queda = cv2.getTickCount() / cv2.getTickFrequency()
                tempo_total = tempo_final_queda - tempo_inicio_queda
                distancia_total_cm = abs(ponto_final_queda - ponto_inicial_queda) * escala_conversao
                velocidade_media = (distancia_total_cm / 100) / tempo_total 
                print(f"Velocidade média: {velocidade_media} m/s")



            # Registra se o objeto cruzou a linha final e calcula a velocidade e a distância
            if passou_linha_final(ponto_inferior_objeto) and tempo_final_queda is None:
                ponto_final_queda = ponto_inferior_objeto
                tempo_final_queda = cv2.getTickCount() / cv2.getTickFrequency()
                tempo_total = tempo_final_queda - tempo_inicio_queda
                distancia_total_cm = abs(ponto_final_queda - ponto_inicial_queda) * escala_conversao
                velocidade_media = (distancia_total_cm / 100) / tempo_total 
                print("Objeto passou pela última linha")
                print(f"Velocidade média: {velocidade_media} m/s")
                print(f"Distância total: {distancia_total_cm} cm")

                tempo_inicio_queda = None
                ponto_inicial_queda = None
                ponto_final_queda = None


            ultima_centro_y = centro_y
            posicao_atual = centro_y
            altura_metros = abs(posicao_inicial - posicao_atual) * escala_conversao / 100  # altura em metros
            posicao_anterior = posicao_atual

            tempo_atual = cv2.getTickCount() / cv2.getTickFrequency()
            tempo_decorrido = tempo_atual - tempo_anterior
            tempo_anterior = tempo_atual

            fps = captura.get(cv2.CAP_PROP_FPS)
            time_between_frames = 1.0 / fps
            #Aplico a forma de torricelli para o calculo da velocidade
            velocidade_torricelli = np.sqrt(2 * 9.64 * altura_metros)
            aceleracao = (velocidade_torricelli - velocidade_maxima_torricelli) / tempo_decorrido

            if velocidade_torricelli > velocidade_maxima_torricelli:
                velocidade_maxima_torricelli = velocidade_torricelli

            texto_velocidade_torricelli = f"Velocidade de queda por Torricelli: {velocidade_torricelli:.2f} m/s"
            texto_velocidade_maxima_torricelli = f"Velocidade máxima de queda por Torricelli: {velocidade_maxima_torricelli:.2f} m/s"
           # cv2.putText(frame, texto_velocidade_torricelli, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
           # cv2.putText(frame, texto_velocidade_maxima_torricelli, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255),2)



    cv2.imshow("Detectando a queda do martelo", frame)
    cv2.setMouseCallback("Detectando a queda do martelo", clicar_calibracao)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    time.sleep(time_between_frames)

df = pd.DataFrame(valores, columns=['Distância (cm)', 'Tempo (s)'])
df.to_excel("valores.xlsx", index=False)
cv2.waitKey(0)
captura.release()
cv2.destroyAllWindows()