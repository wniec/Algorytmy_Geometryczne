import random
import matplotlib.pyplot as plt
import queue
import datetime
import numpy as np
import matplotlib.collections as mcoll
import matplotlib.colors as mcolors
from matplotlib.widgets import Button
import json as js
# Parametr określający jak blisko (w odsetku całego widocznego zakresu) punktu początkowego 
# wielokąta musimy kliknąć, aby go zamknąć.
TOLERANCE = 0.15

def dist(point1, point2):
    return np.sqrt(np.power(point1[0] - point2[0], 2) + np.power(point1[1] - point2[1], 2))

# Klasa ta trzyma obecny stan wykresu oraz posiada metody, które mają zostać wykonane
# po naciśnięciu przycisków.
class _Button_callback(object):
    def __init__(self, scenes):
        self.i = 0
        self.scenes = scenes
        self.adding_points = False
        self.added_points = []
        self.adding_lines = False
        self.added_lines = []
        self.adding_rects = False
        self.added_rects = []

    def set_axes(self, ax):
        self.ax = ax
        
    # Metoda ta obsługuje logikę przejścia do następnej sceny.
    def next(self, event):
        self.i = (self.i + 1) % len(self.scenes)
        self.draw(autoscaling = True)

    # Metoda ta obsługuje logikę powrotu do poprzedniej sceny.
    def prev(self, event):
        self.i = (self.i - 1) % len(self.scenes)
        self.draw(autoscaling = True)
        
    # Metoda ta aktywuje funkcję rysowania punktów wyłączając równocześnie rysowanie 
    # odcinków i wielokątów.
    def add_point(self, event):
        self.adding_points = not self.adding_points
        self.new_line_point = None
        if self.adding_points:
            self.adding_lines = False
            self.adding_rects = False
            self.added_points.append(PointsCollection([]))
            
    # Metoda ta aktywuje funkcję rysowania odcinków wyłączając równocześnie
    # rysowanie punktów i wielokątów.     
    def add_line(self, event):   
        self.adding_lines = not self.adding_lines
        self.new_line_point = None
        if self.adding_lines:
            self.adding_points = False
            self.adding_rects = False
            self.added_lines.append(LinesCollection([]))

    # Metoda ta aktywuje funkcję rysowania wielokątów wyłączając równocześnie
    # rysowanie punktów i odcinków.
    def add_rect(self, event):
        self.adding_rects = not self.adding_rects
        self.new_line_point = None
        if self.adding_rects:
            self.adding_points = False
            self.adding_lines = False
            self.new_rect()
    
    def new_rect(self):
        self.added_rects.append(LinesCollection([]))
        self.rect_points = []
        
    # Metoda odpowiedzialna za właściwą logikę rysowania nowych elementów. W
    # zależności od włączonego trybu dodaje nowe punkty, początek, koniec odcinka
    # lub poszczególne wierzchołki wielokąta. Istnieje ciekawa logika sprawdzania
    # czy dany punkt jest domykający dla danego wielokąta. Polega ona na tym, że
    # sprawdzamy czy odległość nowego punktu od początkowego jest większa od
    # średniej długości zakresu pomnożonej razy parametr TOLERANCE.   
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        new_point = (event.xdata, event.ydata)
        if self.adding_points:
            self.added_points[-1].add_points([new_point])
            self.draw(autoscaling = False)
        elif self.adding_lines:
            if self.new_line_point is not None:
                self.added_lines[-1].add([self.new_line_point, new_point])
                self.new_line_point = None
                self.draw(autoscaling = False)
            else:
                self.new_line_point = new_point
        elif self.adding_rects:
            if len(self.rect_points) == 0:
                self.rect_points.append(new_point)
            elif len(self.rect_points) == 1:
                self.added_rects[-1].add([self.rect_points[-1], new_point])
                self.rect_points.append(new_point)
                self.draw(autoscaling = False)
            elif len(self.rect_points) > 1:
                if dist(self.rect_points[0], new_point) < (np.mean([self.ax.get_xlim(), self.ax.get_ylim()])*TOLERANCE):
                    self.added_rects[-1].add([self.rect_points[-1], self.rect_points[0]])
                    self.new_rect()
                else:    
                    self.added_rects[-1].add([self.rect_points[-1], new_point])
                    self.rect_points.append(new_point)
                self.draw(autoscaling = False)
    
    # Metoda odpowiedzialna za narysowanie całego wykresu. Warto zauważyć,
    # że zaczyna się ona od wyczyszczenia jego wcześniejszego stanu. Istnieje w
    # niej nietrywialna logika zarządzania zakresem wykresu, tak żeby, w zależności
    # od ustawionego parametru autoscaling, uniknąć sytuacji, kiedy dodawanie
    # nowych punktów przy brzegu obecnie widzianego zakresu powoduje niekorzystne
    # przeskalowanie.
    def draw(self, autoscaling = True):
        if not autoscaling:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
        self.ax.clear()
        for collection in (self.scenes[self.i].points + self.added_points):
            if len(collection.points) > 0:
                self.ax.scatter(*zip(*(np.array(collection.points))), **collection.kwargs)
        for collection in (self.scenes[self.i].lines + self.added_lines + self.added_rects):
            self.ax.add_collection(collection.get_collection())
        self.ax.autoscale(autoscaling)
        if not autoscaling:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
        plt.draw()
# Klasa Scene odpowiada za przechowywanie elementów, które mają być
# wyświetlane równocześnie. Konkretnie jest to lista PointsCollection i
# LinesCollection.
class Scene:
    def __init__(self, points=[], lines=[]):
        self.points=points
        self.lines=lines

# Klasa PointsCollection gromadzi w sobie punkty jednego typu, a więc takie,
# które zostaną narysowane w takim samym kolorze i stylu. W konstruktorze
# przyjmuje listę punktów rozumianych jako pary współrzędnych (x, y). Parametr
# kwargs jest przekazywany do wywołania funkcji z biblioteki MatPlotLib przez
# co użytkownik może podawać wszystkie parametry tam zaproponowane.        
class PointsCollection:
    def __init__(self, points, **kwargs):
        self.points = points
        self.kwargs = kwargs
    
    def add_points(self, points):
        self.points = self.points + points

# Klasa LinesCollection podobnie jak jej punktowy odpowiednik gromadzi
# odcinki tego samego typu. Tworząc ją należy podać listę linii, gdzie każda
# z nich jest dwuelementową listą punktów – par (x, y). Parametr kwargs jest
# przekazywany do wywołania funkcji z biblioteki MatPlotLib przez co użytkownik
# może podawać wszystkie parametry tam zaproponowane.
class LinesCollection:
    def __init__(self, lines, **kwargs):
        self.lines = lines
        self.kwargs = kwargs
        
    def add(self, line):
        self.lines.append(line)
        
    def get_collection(self):
        return mcoll.LineCollection(self.lines, **self.kwargs)

# Klasa Plot jest najważniejszą klasą w całym programie, ponieważ agreguje
# wszystkie przygotowane sceny, odpowiada za stworzenie wykresu i przechowuje
# referencje na przyciski, dzięki czemu nie będą one skasowane podczas tzw.
# garbage collectingu.
class Plot:
    def __init__(self, scenes = [Scene()], points = [], lines = [], json = None):
        if json is None:
            self.scenes = scenes
            if points or lines:
                self.scenes[0].points = points
                self.scenes[0].lines = lines
        else:
            self.scenes = [Scene([PointsCollection(pointsCol) for pointsCol in scene["points"]], 
                                 [LinesCollection(linesCol) for linesCol in scene["lines"]]) 
                           for scene in js.loads(json)]
    
    # Ta metoda ma szczególne znaczenie, ponieważ konfiguruje przyciski i
    # wykonuje tym samym dość skomplikowaną logikę. Zauważmy, że konfigurując każdy
    # przycisk podajemy referencję na metodę obiektu _Button_callback, która
    # zostanie wykonana w momencie naciśnięcia.
    def __configure_buttons(self):
        plt.subplots_adjust(bottom=0.2)
        ax_prev = plt.axes([0.6, 0.05, 0.15, 0.075])
        ax_next = plt.axes([0.76, 0.05, 0.15, 0.075])
        ax_add_point = plt.axes([0.44, 0.05, 0.15, 0.075])
        ax_add_line = plt.axes([0.28, 0.05, 0.15, 0.075])
        ax_add_rect = plt.axes([0.12, 0.05, 0.15, 0.075])
        b_next = Button(ax_next, 'Następny')
        b_next.on_clicked(self.callback.next)
        b_prev = Button(ax_prev, 'Poprzedni')
        b_prev.on_clicked(self.callback.prev)
        b_add_point = Button(ax_add_point, 'Dodaj punkt')
        b_add_point.on_clicked(self.callback.add_point)
        b_add_line = Button(ax_add_line, 'Dodaj linię')
        b_add_line.on_clicked(self.callback.add_line)
        b_add_rect = Button(ax_add_rect, 'Dodaj figurę')
        b_add_rect.on_clicked(self.callback.add_rect)
        return [b_prev, b_next, b_add_point, b_add_line, b_add_rect]
    
    def add_scene(self, scene):
        self.scenes.append(scene)
    
    def add_scenes(self, scenes):
        self.scenes = self.scenes + scenes

    # Metoda toJson() odpowiada za zapisanie stanu obiektu do ciągu znaków w
    # formacie JSON.
    def toJson(self):
        return js.dumps([{"points": [np.array(pointCol.points).tolist() for pointCol in scene.points], 
                          "lines":[linesCol.lines for linesCol in scene.lines]} 
                         for scene in self.scenes])    
    
    # Metoda ta zwraca punkty dodane w trakcie rysowania.
    def get_added_points(self):
        if self.callback:
            return self.callback.added_points
        else:
            return None
    
    # Metoda ta zwraca odcinki dodane w trakcie rysowania.
    def get_added_lines(self):
        if self.callback:
            return self.callback.added_lines
        else:
            return None
        
    # Metoda ta zwraca wielokąty dodane w trakcie rysowania.
    def get_added_figure(self):
        if self.callback:
            return self.callback.added_rects
        else:
            return None
    
    # Metoda ta zwraca punkty, odcinki i wielokąty dodane w trakcie rysowania
    # jako scenę.
    def get_added_elements(self):
        if self.callback:
            return Scene(self.callback.added_points, self.callback.added_lines+self.callback.added_rects)
        else:
            return None
    
    # Główna metoda inicjalizująca wyświetlanie wykresu.
    def draw(self):
        plt.close()
        fig = plt.figure()
        self.callback = _Button_callback(self.scenes)
        self.widgets = self.__configure_buttons()
        ax = plt.axes(autoscale_on = False)
        self.callback.set_axes(ax)
        fig.canvas.mpl_connect('button_press_event', self.callback.on_click)
        plt.show()
        self.callback.draw()
###################################################################################################
def Det(A,B,C):
    # Funkcja określająca wzajemne położenie 3 kolejnych punktów
    a=A[0]*B[1]
    b=B[0]*C[1]
    c=C[0]*A[1]
    d=B[1]*C[0]
    e=C[1]*A[0]
    f=A[1]*B[0]
    return a+b+c-(d+e+f)
def classify(pointSet):
    p=pointSet[0]
    pointSet.append(p)
    begin=[p]
    end=[]
    divide=[]
    merge=[]
    default=[]
    lines=[]
    n=len(pointSet)
    for i in range(1,n-1):
        y=pointSet[i][1]
        d=Det(pointSet[i-1],pointSet[i],pointSet[i+1])
        lines.append((pointSet[i-1],pointSet[i]))
        if d>=0 and y>pointSet[i+1][1] and y>pointSet[i-1][1]:
            begin.append(pointSet[i])
        elif d>=0 and y<pointSet[i+1][1] and y<pointSet[i-1][1]:
            end.append(pointSet[i])
        elif d<0 and y>pointSet[i+1][1] and y>pointSet[i-1][1]:
            divide.append(pointSet[i])
        elif d<0 and y<pointSet[i+1][1] and y<pointSet[i-1][1]:
            merge.append(pointSet[i])
        else:
            default.append(pointSet[i])
    lines.append((pointSet[n-2],pointSet[n-1]))
    pointSet.pop(-1)
    return(begin,end,divide,merge,default,lines)
def classifyShow(pointSet):
    begin,end,divide,merge,default,lines=classify(pointSet)
    return Scene([PointsCollection(begin,color='green'),PointsCollection(end,color='red'),PointsCollection(merge,color='purple'),PointsCollection(divide,color='blue'),PointsCollection(default,color='grey')],[LinesCollection(lines,color='grey')])
def getpoints(pointSet):
    #Funkcja zwraca punkty uszeregowane według wskazówek zegaraod leżącego najwyżej
    #oraz indeks najniższego punktu w takim uszeregowaniu
    n=len(pointSet)
    wmax=pointSet[0]
    wmin=pointSet[0]
    imax,imin,i=0,0,0
    for pS in pointSet:
        if pS[1]>wmax[1]:
            wmax=pS
            imax=i
        elif pS[1]<wmin[1]:
            wmin=pS
            imin=i
        i+=1
    if imax<imin:
        return (pointSet[imax:]+pointSet[:imax],imin-imax)
    else:
        return (pointSet[imax:]+pointSet[:imax],n-imax+imin)
def valid(pS,A,B,C):
    #sprawdzenie, czy trójkąt A B C leży
    #wewnątrz triangulowanrgo wielokąta monotonicznego
    d = Det(pS[A[0]], pS[B[0]], pS[C[0]])
    s=int(A[1])*2-1
    return s*d<0
def triangulate(pS,imin,scenes):
    #Triangulacja wielokąta monotonicznego
    n=len(pS)
    stack=queue.LifoQueue()
    left=[(i,True) for i in range(imin)]
    right=[(i,False)for i in range(n-1,imin-1,-1)]
    l,r=0,0
    vertices=[]
    for i in range(n):
        if l<len(left) and pS[left[l][0]][1]>pS[right[r][0]][1]:
            vertices.append(left[l])
            l+=1
        else:
            vertices.append(right[r])
            r+=1
    triangles=[]
    stack.put(vertices[0])
    stack.put(vertices[1])
    for i in range(2,n):
        A=vertices[i]
        B=stack.get()
        C=stack.get()
        if (A[1]!=B[1] or i==n-1):
            #Gdy wierzchołki są na różnych "gałęziach" wielokąta, lub wierzchołek jest najniższym w wielokącie
            last=B
            triangles.append((pS[A[0]],pS[B[0]],pS[C[0]]))
            scenes.append(makeTriangulateScene(triangles.copy(),pS))
            while not stack.empty():
                B=C
                C=stack.get()
                triangles.append((pS[A[0]],pS[B[0]],pS[C[0]]))
                scenes.append(makeTriangulateScene(triangles.copy(),pS))
            stack.put(last)
            stack.put(A)
        else:
            toput=[]
            while True:
                if valid(pS,A,B,C):
                    triangles.append((pS[A[0]], pS[B[0]], pS[C[0]]))
                    scenes.append(makeTriangulateScene(triangles.copy(),pS))
                else:
                    toput.append(B)
                if not stack.empty():
                    B=C
                    C=stack.get()
                else:
                    break
            t=len(toput)
            stack.put(C)
            for i in range(t-1,-1,-1):
                stack.put(toput[i])
            stack.put(A)
    return triangles
def makeTriangulateScene(triangles,pS):
    lines1=set()
    lines2=[]
    for triangle in triangles:
        lines1.add((triangle[0],triangle[1]))
        lines1.add((triangle[1],triangle[2]))
        lines1.add((triangle[0],triangle[2]))
    n=len(pS)
    for i in range(n):
        if not( (pS[i-1],pS[i]) in lines1) and (not(pS[i],pS[i-1]) in lines1):
            lines2.append((pS[i-1],pS[i]))
    return Scene([PointsCollection(pS)],[LinesCollection(list(lines1),color='blue'),LinesCollection(lines2,color='grey')])
def makeDivideScene(diagonals,v,ps):
    y=v[1]
    broom=((0,y),(1,y))
    lines=[]
    diags=[]
    for d in diagonals:
        diags.append((pS[d[0]],pS[d[1]]))
    n=len(pS)
    for i in range(n):
        lines.append((pS[i-1],pS[i]))
    return Scene([PointsCollection(pS)],[LinesCollection([broom],color='black'),LinesCollection(lines,color='grey'),LinesCollection(diags,color='red')])
def divide_classify(pS):
    #klasyfikacja wierzchołków dla potrzeb funkcji divide
    begin,end,divide,merge,default,lines=classify(pS)
    m=[begin,end,divide,merge,default]
    n=len(pS)
    classified=[]
    it=[0,0,0,0,0]
    for i in range (n):
        for j in range(5):
            if it[j]<len(m[j]) and m[j][it[j]]==pS[i]:
                classified.append((pS[i][0],pS[i][1],j,i))
                it[j]+=1
                break
    classified.sort(key=lambda x: -x[1])
    for l in lines:
        if l[0][1]<l[1][1]:
            l=(l[1],l[0])
    return classified,lines
def divide(pS,scenes):
    classified,lines=divide_classify(pS)
    eventStruct=queue.Queue()
    diagonals=[]
    statestruct={}
    for c in classified:
        eventStruct.put(c)#Wstawiam do kolejki kolejne wierzcholki
    while not eventStruct.empty():
        v=eventStruct.get()#Wyjmuję wierzchołek z kolejki
        scenes.append(makeDivideScene(diagonals.copy(),v,pS))
        if v[2]==0:
            #początkowy
            el=lines[v[3]]
            statestruct[el]=v
        elif v[2]==1:
            #końcowy
            el=lines[v[3]-1]
            helper=statestruct.get(el)
            if helper[2]==3:
                diagonals.append((v[3],helper[3]))
            statestruct.pop(el)
        elif v[2]==2:
            #dzielący
            ev=find_left(statestruct,(v[0],v[1]))
            helper=statestruct.get(ev)
            diagonals.append((v[3],helper[3]))
            statestruct[ev]=v
            ep=lines[v[3]]
            statestruct[ep]=v
        elif v[2]==3:
            #łączący
            ep=lines[v[3]-1]
            helper=statestruct.get(ep)
            if helper[2]==3:
                diagonals.append((v[3],helper[3]))
            statestruct.pop(ep)
            ev=find_left(statestruct,(v[0],v[1]))
            helper=statestruct.get(ev)
            if helper[2]==3:
                diagonals.append((v[3],helper[3]))
            statestruct[ev]=v
        elif v[2]==4:
            #prawidłowy
            eg=lines[v[3]-1]
            ed=lines[v[3]]
            if eg in statestruct:
                helper=statestruct.get(eg)
                if helper[2]==3:
                    diagonals.append((v[3],helper[3]))
                statestruct.pop(eg)
                statestruct[ed]=v
            else:
                ev=find_left(statestruct,(v[0],v[1]))
                helper=statestruct.get(ev)
                if helper[2]==3:
                    diagonals.append((v[3],helper[3]))
                statestruct[ev]=v
    return diagonals
def find_left(statestruct,point):
    keys=list(statestruct.keys())
    cur_left=None
    for k in keys:
        if Det(k[0],k[1],point)>10**(-12) and (cur_left==None or Det(cur_left[0],cur_left[1],k[0])>10**(-12)):
            cur_left = k
    return cur_left
def makeMonotonicTab(pS,scenes):
    #Dzielę wielokąt na wielokąty monotoniczne, wykorzystując jego podział przekątnymi
    diags=divide(pS,scenes)#zbiór przekątnych dzielących wielokąt na wielokąty monotoniczne
    d=len(diags)
    diagonals=[]
    for i in range(d):
        b,e=diags[i]
        x=(min(b,e),max(b,e))
        diagonals.append(x)
    diagonals.sort(key=lambda x: x[1]-x[0])
    #ukierunkowałem przekątne przeciwnie do ruchu wskazówek zegara
    #posortowałem przekątne po "długości"(liczbie wierzchołków, które odcinają)
    used=[False for p in pS]
    #lista wykorzystanych wierzcholków
    monotonic=[]
    for i in range(d):
        begin=diagonals[i][0]
        end=diagonals[i][1]
        m=[pS[begin]]
        for u in range(begin+1,end):
            if not used[u]:
                m.append(pS[u])
                used[u]=True
        m.append(pS[end])
        monotonic.append(m)
    us=len(used)
    m=[]
    for j in range(us):
        if not used[j]:
            m.append(pS[j])
    monotonic.append(m)
    #zwracam listę list wierzchołków w poszczególnych wielokątach monotonicznych
    return monotonic
def triangulateMonotonic(pS):
    scenes=[]
    monotonic=makeMonotonicTab(pS,scenes)
    triangles=[]
    p=[]
    l=[]
    i=0
    for m in monotonic:
        mSet,imin=getpoints(m)
        triangles= triangulate(mSet,imin,scenes)
        #wstawianie do odpowiednio list wierzchołków i krawędzi całych trójkątów.
        for triangle in triangles:
            p.append(triangle[0])
            p.append(triangle[1])
            p.append(triangle[2])
            l.append([triangle[0],triangle[1]])
            l.append([triangle[2],triangle[1]])
            l.append([triangle[0],triangle[2]])
    scene=Scene([PointsCollection(p,color='blue')],[LinesCollection(l,color='blue')])
    scenes.append(scene)
    return scenes
plot1 = Plot()
plot1.draw()
l=plot1.get_added_figure()
li=l[0].lines
pointSet=[p[0] for p in li]
pS,imin=getpoints(pointSet)
scenes=triangulateMonotonic(pS)
plot=Plot(scenes)
plot.draw()
