import pygame
import random
import copy
import sys
import time

# Inicialização dos subsistemas do Pygame
pygame.init()
pygame.mixer.init()

# Constantes de configuração da janela e grid
LARGURA, ALTURA = 540, 600
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Sudoku")
VOLUME_GLOBAL= 0.1

# Paleta de cores (padrão RGB)
BRANCO = (255, 255,255)
PRETO = (0, 0, 0)
CINZA = (128, 128, 128)
AZUL = (0, 0, 255)
VERMELHO = (255, 0, 0)
VERDE = (0, 200, 0)

# Instanciação de fontes na memória
FONTE_PRINCIPAL = pygame.font.SysFont("comicsans", 40)
FONTE_NOTAS = pygame.font.SysFont("comicsans", 20)
FONTE_MENU = pygame.font.SysFont("comicsans", 50)

def tocar_musica(faixa, loop=-1):
    """Gerencia o stream de áudio do Pygame."""
    try:
        pygame.mixer.music.load(f"ativos/{faixa}.mp3") 
        pygame.mixer.music.set_volume(VOLUME_GLOBAL)
        pygame.mixer.music.play(loop)
    except pygame.error:
        print(f"Aviso: Não foi possível carregar ativos/{faixa}.mp3.")

def gerar_tabuleiro(dificuldade):
    #tabuleiro completo
    base = [
        [5,3,4,6,7,8,9,1,2], [6,7,2,1,9,5,3,4,8], [1,9,8,3,4,2,5,6,7],
        [8,5,9,7,6,1,4,2,3], [4,2,6,8,5,3,7,9,1], [7,1,3,9,2,4,8,5,6],
        [9,6,1,5,3,7,2,8,4], [2,8,7,4,1,9,6,3,5], [3,4,5,2,8,6,1,7,9]
    ]
    #algoritmo de aleatoriedade
    for _ in range(10):
        bloco = random.randint(0, 2) * 3
        r1, r2 = bloco + random.randint(0, 2), bloco + random.randint(0, 2)
        base[r1], base[r2] = base[r2], base[r1]
        base = list(map(list, zip(*base))) 
        bloco = random.randint(0, 2) * 3
        r1, r2 = bloco + random.randint(0, 2), bloco + random.randint(0, 2)
        base[r1], base[r2] = base[r2], base[r1]
        base = list(map(list, zip(*base)))
    solucao = copy.deepcopy(base)
    quebra_cabeca = copy.deepcopy(base)
    #ajuste de dificuldade
    remocoes = {"Fácil": 30, "Médio": 45, "Difícil": 55}
    qtd_remover = remocoes.get(dificuldade, 40)
    while qtd_remover > 0:
        linha, col = random.randint(0, 8), random.randint(0, 8)
        if quebra_cabeca[linha][col] != 0:
            quebra_cabeca[linha][col] = 0
            qtd_remover -= 1
    return quebra_cabeca, solucao

class Celula: # roda no inicio do game 
    def __init__(self, valor, linha, col, solucao_valor):
        self.valor = valor # armazena o numero 
        self.solucao_valor = solucao_valor # guarda o valor do tabuleiro
        #coordenadas da celula 
        self.linha = linha 
        self.col = col
        
        self.nota = 0 # espaço para marcação temporaria 
        #jogador clicou na celula
        self.selecionada = False
        self.editavel = (valor == 0)

    def desenhar(self, tela):
        espaco = LARGURA / 9
        x, y = self.col * espaco, self.linha * espaco
        if self.valor != 0:
            if not self.editavel: cor = PRETO # verifica se a celula é editavel
            elif self.valor == self.solucao_valor: cor = AZUL
            else: cor = VERMELHO
            texto = FONTE_PRINCIPAL.render(str(self.valor), 1, cor)
            tela.blit(texto, (x + (espaco/2 - texto.get_width()/2), y + (espaco/2 - texto.get_height()/2)))
        #desenho dos numeros do modo notas
        elif self.nota != 0:
            texto = FONTE_NOTAS.render(str(self.nota), 1, CINZA)
            tela.blit(texto, (x + 5, y + 5))

        if self.selecionada: pygame.draw.rect(tela, VERMELHO, (x, y, espaco, espaco), 3)

class Tabuleiro: # gerenciador das celulas 
    def __init__(self, dificuldade):
        self.matriz_jogo, self.matriz_solucao = gerar_tabuleiro(dificuldade)
        self.celulas = [[Celula(self.matriz_jogo[i][j], i, j, self.matriz_solucao[i][j]) for j in range(9)] for i in range(9)]
        self.selecionado = None
        self.erros = 0
        self.modo_notas = False # modo notas , inicia desligado 

    def movimento_valido(self, num, linha, col):#percorre a linha , coluna e o bloco 3x3
        for j in range(9):
            if self.celulas[linha][j].valor == num: return False
        for i in range(9):
            if self.celulas[i][col].valor == num: return False
        inicio_linha, inicio_col = (linha // 3) * 3, (col // 3) * 3
        for i in range(inicio_linha, inicio_linha + 3):
            for j in range(inicio_col, inicio_col + 3):
                if self.celulas[i][j].valor == num: return False
        return True

    def desenhar(self, tela):# desenha as grids e pede para cada celula 
        espaco = LARGURA / 9
        for i in range(10):
            espessura = 4 if i % 3 == 0 and i != 0 else 1
            pygame.draw.line(tela, PRETO, (0, i * espaco), (LARGURA, i * espaco), espessura)
            pygame.draw.line(tela, PRETO, (i * espaco, 0), (i * espaco, LARGURA), espessura)
        for i in range(9):
            for j in range(9): self.celulas[i][j].desenhar(tela)

    def selecionar(self, linha, col):
        for i in range(9):
            for j in range(9): self.celulas[i][j].selecionada = False
        self.celulas[linha][col].selecionada = True
        self.selecionado = (linha, col)

    def inserir_numero(self, num):#decide se o numero é contado como erro ou atualiza o valor da celula
        if self.selecionado:
            linha, col = self.selecionado
            celula = self.celulas[linha][col]
            #ignora as regras de validação se o modo estiver ativo 
            if celula.editavel and celula.valor == 0:
                if self.modo_notas: celula.nota = num # se estiver ligado armezena o numero na varialvel nota
                else:
                    if not self.movimento_valido(num, linha, col):#tenta colocar um numero ja existente 
                        self.erros += 1
                        celula.valor = num
                    elif num != celula.solucao_valor: # numero errado em relação a solução final
                        self.erros += 1
                        celula.valor = num
                    else:
                        celula.valor = num

    def deletar(self):
        if self.selecionado:
            linha, col = self.selecionado
            celula = self.celulas[linha][col]
            if celula.editavel: celula.valor = 0; celula.nota = 0

    def verificar_vitoria(self):#comparação de celulas entre jogador e tabuleiro
        for i in range(9):
            for j in range(9):
                if self.celulas[i][j].valor != self.celulas[i][j].solucao_valor: return False
        return True

def desenhar_texto_centralizado(texto, fonte, cor, y_offset=0):
    render = fonte.render(texto, 1, cor)
    x, y = LARGURA/2 - render.get_width()/2, ALTURA/2 - render.get_height()/2 + y_offset
    TELA.blit(render, (x, y))
    return pygame.Rect(x, y, render.get_width(), render.get_height())

def tela_inicial():
    tocar_musica("menu")
    btn_jogar = pygame.Rect(0, 0, 0, 0)
    btn_sair = pygame.Rect(0, 0, 0, 0)
    while True:
        TELA.fill(BRANCO)
        desenhar_texto_centralizado("SUDOKU", FONTE_MENU, PRETO, -100)
        pos = pygame.mouse.get_pos()
        cor_jogar = VERDE if btn_jogar.collidepoint(pos) else (0, 150, 0)
        cor_sair = VERMELHO if btn_sair.collidepoint(pos) else (150, 0, 0)
        #detector de colisão
        btn_jogar = desenhar_texto_centralizado("Jogar", FONTE_PRINCIPAL, cor_jogar, 0)
        btn_sair = desenhar_texto_centralizado("Sair", FONTE_PRINCIPAL, cor_sair, 80)
        pygame.display.update()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit() # quit
            if evento.type == pygame.MOUSEBUTTONDOWN:# condição para proxima tela
                if btn_jogar.collidepoint(pos): return "Jogar"
                if btn_sair.collidepoint(pos): pygame.quit(); sys.exit() 

def tela_menu():
    btn_facil = pygame.Rect(0, 0, 0, 0)
    btn_medio = pygame.Rect(0, 0, 0, 0)
    btn_dificil = pygame.Rect(0, 0, 0, 0)
    while True:
        TELA.fill(BRANCO)
        desenhar_texto_centralizado("DIFICULDADE", FONTE_MENU, PRETO, -150)
        pos = pygame.mouse.get_pos()
        cor_facil = (0, 255, 0) if btn_facil.collidepoint(pos) else (0, 150, 0)
        cor_medio = (255, 200, 0) if btn_medio.collidepoint(pos) else (200, 120, 0)
        cor_dificil = (255, 50, 50) if btn_dificil.collidepoint(pos) else (150, 0, 0)
        #detector de colisão (efeito do mouse)
        btn_facil = desenhar_texto_centralizado("Fácil", FONTE_PRINCIPAL, cor_facil, -20)
        btn_medio = desenhar_texto_centralizado("Médio", FONTE_PRINCIPAL, cor_medio, 40)
        btn_dificil = desenhar_texto_centralizado("Difícil", FONTE_PRINCIPAL, cor_dificil, 100)
        pygame.display.update()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit() # quit pelo x 
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE: return None # voltar com o esc
            if evento.type == pygame.MOUSEBUTTONDOWN:#condição para entrar na proxima tela
                if btn_facil.collidepoint(pos): return "Fácil"
                if btn_medio.collidepoint(pos): return "Médio"
                if btn_dificil.collidepoint(pos): return "Difícil"

def tela_fim(mensagem, cor, som):
    tocar_musica(som, 0) 
    btn_recomecar = pygame.Rect(0, 0, 0, 0)
    btn_menu = pygame.Rect(0, 0, 0, 0)
    while True:
        TELA.fill(BRANCO)
        desenhar_texto_centralizado(mensagem, FONTE_MENU, cor, -70)
        pos = pygame.mouse.get_pos()
        cor_rec = AZUL if btn_recomecar.collidepoint(pos) else PRETO
        cor_menu = AZUL if btn_menu.collidepoint(pos) else PRETO
        #detector de colisão
        btn_recomecar = desenhar_texto_centralizado("Recomeçar", FONTE_PRINCIPAL, cor_rec, 20)
        btn_menu = desenhar_texto_centralizado("Voltar ao Menu", FONTE_PRINCIPAL, cor_menu, 80)
        pygame.display.update()
        for evento in pygame.event.get():#eventos para passar de tela
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if btn_recomecar.collidepoint(pos): return "recomecar"
                if btn_menu.collidepoint(pos): return "menu"

def jogar():#marquina de estados
    while True:#loop externo
        if tela_inicial() == "Jogar":
            
            while True:# loop intermediario
                dificuldade = tela_menu()
                if not dificuldade: break # ESC volta para o menu inicial
                
                while True:# loop interno
                    tabuleiro = Tabuleiro(dificuldade)
                    jogando = True
                    tempo_inicio = time.time()
                    tocar_musica("game")
                    acao_fim = "menu"
                    
                    while jogando: # loop de renderização
                        TELA.fill(BRANCO)
                        tabuleiro.desenhar(TELA)
                        tempo_limite=400
                        tempo_decorrido = tempo_limite- int(time.time() - tempo_inicio)
                        m, s = tempo_decorrido // 60, tempo_decorrido % 60
                        if tempo_decorrido <= 0:
                                jogando = False
                        
                        # terminal da tela no estado jogo
                        TELA.blit(FONTE_NOTAS.render(f"Erros: {tabuleiro.erros}/10", 1, VERMELHO), (20, 550))
                        TELA.blit(FONTE_NOTAS.render("ESC: Voltar", 1, PRETO), (20, 575))
                        TELA.blit(FONTE_NOTAS.render(f"Tempo: {m:02}:{s:02}", 1, PRETO), (220, 550))
                        TELA.blit(FONTE_NOTAS.render(f"(N)Notas: {'ON' if tabuleiro.modo_notas else 'OFF'}", 1, CINZA if tabuleiro.modo_notas else PRETO), (220, 575))
                        
                        pygame.display.update()
                        if tabuleiro.erros >= 10:
                            acao_fim = tela_fim("GAME OVER", VERMELHO, "derrota_1")
                            jogando = False
                        elif tabuleiro.verificar_vitoria():
                            acao_fim = tela_fim("VITÓRIA!", VERDE, "vitoria_1")
                            jogando = False
                        for evento in pygame.event.get():
                            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()# se o tipo de eventor for "feche a janela"
                            # selecionar a posição com mouse 
                            if evento.type == pygame.MOUSEBUTTONDOWN:
                                pos = pygame.mouse.get_pos()
                                if pos[1] < LARGURA: tabuleiro.selecionar(int(pos[1] // (LARGURA / 9)), int(pos[0] // (LARGURA / 9)))#divisão de inteiros
                            
                            if evento.type == pygame.KEYDOWN:#comandos de teclas no estado jogo
                                if evento.key == pygame.K_ESCAPE: acao_fim = "menu"; jogando = False # 
                                if evento.key == pygame.K_n: tabuleiro.modo_notas = not tabuleiro.modo_notas # modo notas(operador not)
                                if evento.key == pygame.K_DELETE or evento.key == pygame.K_BACKSPACE: tabuleiro.deletar() # função de delete
                                if pygame.K_1 <= evento.key <= pygame.K_9: tabuleiro.inserir_numero(evento.key - pygame.K_0) # teclas de 1 a 9 
                                elif pygame.K_KP1 <= evento.key <= pygame.K_KP9: tabuleiro.inserir_numero(evento.key - pygame.K_KP1 + 1)
                    if acao_fim == "menu": break # se i status final for 'menu', quebre o loop de jogo e retorne ao menu inicial

if __name__ == "__main__":
    jogar()