# Bibliotheken importieren

# Standard-Bibliotheken
import sys, csv
import numpy as np 
import zipfile
import re

from PIL import Image
from time import sleep
from datetime import datetime

# SciPy
from scipy.signal import medfilt2d
from scipy import signal
from scipy.ndimage import spline_filter

# Matplotlib
import matplotlib.pyplot as plt

from matplotlib import cm
from matplotlib.pyplot import figure
from matplotlib.colors import ListedColormap
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from mpl_toolkits.mplot3d import Axes3D

# PyQt5 für die GUI
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from PyQt5.QtWidgets import QDialog, QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QLabel
from PyQt5.QtGui import QIcon, QPixmap

from PyQt5.uic import loadUi

# Globale Variablen:

# Dateiauswahl
dateiauswahl = ''
solldaten = ''

neuauswahl = 0

dateiInfo = [None] * 3   # dateiname, zeile, spalte

# Startverzeichnis
startDir = '/home/ian/Dokumente/Semester_7/Seminar 2.2/BigData/'

# Speicherung
plotSpeichern = 0
datenSpeichern = 0

# Matrixinformationen
pixelgroesse = ''
einheit = ''

# Terminal
terminalLogs = list()
j = 0

# Eindrucksvolle Daten: 
# G_0005, A__0004, D_0004, E_0001, C_0206, J_0796

# To-Do:
# solldaten abziehen

# BugFix:
# L-Filter geht noch nicht
# Abgeänderte Messwerte werden bei S-Filter nicht angezeigt

# Klasse stellt Hauptanwendung zur verfügung
class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # GUI-Datei laden
        uic.loadUi("gui.ui", self)

        # Fenstergröße festlegen
        self.setFixedSize(810, 737)
        # Fenster Icon festlegen
        self.setWindowIcon(QIcon('tu-kaiserslautern-squarelogo.png'))        
        # TU-Logo als Banner festlegen
        self.TUlogo.setIcon(QIcon('tu_logo.png')) 
        
        # Textfarbe ändern
        #self.terminalOut.setStyleSheet("color: green;")

        # Terminal Ausgabe, Programmstart ankündigen
        self.log("Programmstart")
        self.log("Bitte Messwerte einlesen / entpacken")

        # Hauptfunktion starten
        self.main()
        
    # Logfunktion, Terminalausgabe
    def log(self, text):
        global terminalLogs; global j 

        # Uhrzeit abfragen, H:M:S
        now = datetime.now()
        current_timestamp = now.strftime("%H:%M:%S")

        # Log-Text zusammensetzen
        logText = '['+current_timestamp+'] ' + text

        # Text im Terminal-Fenster anzeigen
        terminalLogs.append(logText)

        self.terminalOut.append(str(logText))
        print(str(logText))
        j += 1
        
    # .zip entpacken
    def entzip(self):
        global startDir
        
        # getOpenFileName<s> für mehrere Dateien
        # Dialog öffnen, nur csv-Dateien auswählbar
        zipDatei = QFileDialog.getOpenFileNames(self, 'Daten zum entpacken', startDir, "ZIP-Dateien (*.zip)")

        # Wenn zipDatei ausgewählt..
        if not (zipDatei[0] == ''):
            self.log("Entpacken gestartet")

            # Anzahl ausgewählter Dateien
            anzahlAuswahl = len(zipDatei[0]) 

            # Jede ausgewählte Datei entpacken
            for i in range(0, anzahlAuswahl):
                datei = str(zipDatei[0][i])
               
                with zipfile.ZipFile(datei,'r') as zfile:
                    zfile.extractall(startDir)
                
                self.log(str(datei[-5:])+" wurde entpackt")               
        else:
            return 0

    # Plots speichern
    def plotExport(self):
        global plotSpeichern

        # Überprüfen ob Häkchen gesetzt ist
        if (self.savePlot.isChecked()):
            plotSpeichern = 1
            self.log("Plott wird exportiert")
        else:
            self.log("Plott wird NICHT exportiert")

    # Filter-Daten exportieren    
    def datenExport(self):
        global datenSpeichern

        # Überprüfen ob Häkchen gesetzt ist
        if (self.saveData.isChecked()):
            datenSpeichern = 1
            self.log("Daten werden exportiert")
        else:
            self.log("Daten werden NICHT exportiert")

    # Berechnung der Rauheit
    def rauheit(self):
        global dateiauswahl
        global dateiInfo
        global neuauswahl
                
        if not (dateiauswahl == ''):
            neuauswahl = 1
            
            self.log("Rauheit wird berechnet")

            # Messdaten einlesen
            messdatenRaw = np.loadtxt(open(dateiauswahl, "rb"), delimiter=",", skiprows=2, encoding='utf-8')

            # Zeilen, Spalten
            M = int(dateiInfo[1])
            N = int(dateiInfo[2])

            betrag1 = 0.0; betrag2 = 0.0

            z = 0.0
            
            # Mittelwert berechnen 
            for m in range(1,M):
                for n in range(1,N):
                    z += float(messdatenRaw[m,n])
        
            mittelwert = ( 1 / (M*N) ) * z

            # Mittenrauheit Sa berechnen
            for m in range(1,M):
                for n in range(1,N):
                    betrag1 += abs(float(messdatenRaw[m,n]) - mittelwert)

            mittenrauheitSa = (1/(M*N)) * betrag1

            # Quadratrauheit Sq berechnen
            for m in range(1,M):
                for n in range(1,N):
                    betrag2 += (float(messdatenRaw[m,n]) - mittelwert) ** 2

            quadratrauheitSq = np.sqrt((1/(M*N)) * betrag2)

            # Rauheitswerte in jeweiler Text-Box anzeigen
            self.mittenrauwertSa.setText("Sa = " + str(mittenrauheitSa))
            self.quadratrauwertSq.setText("Sq = " + str(quadratrauheitSq))
            # gemittelte Rautiefe Rz ist mittlerweile als ISO-Kennwert gelöscht
        else:
            self.log("Bitte Datei einlesen!")

    # Filter ermitteln und anwenden   
    def filter(self, dateiauswahl):
        global pixelgroesse; global einheit
        global plotSpeichern; global datenSpeichern
        global dateiInfo; global solldaten

        # Prüfung, ob Datei eingelesen
        if not (dateiauswahl == ''):
            # Dateiname erstellen, ohne Endung (csv)
            dateiname = (dateiauswahl.split("/")[-1]).split(".csv")[0]

            # Datei einlesen
            messdatenRaw = np.loadtxt(open(dateiauswahl, "rb"), delimiter=",", skiprows=2, encoding='utf-8')

            # Solldaten einlesen
            solldaten_raw = np.loadtxt(open(solldaten, "rb"), delimiter=",", skiprows=2, encoding='utf-8')

            # Medfilt (Ausreißer)   
            if (self.radio_medfilter.isChecked()):
                # Filtername
                filtername = 'Medfilt'

                # Dateiendung festlegen
                dateiendung = '_medfilt'

                # Plott-Überschrift festlegen
                datenTitelFilter = 'Filter: Medfilt'

                # Filter Medfilt anwenden
                messdatenFilter = medfilt2d(messdatenRaw, kernel_size=3)
            # Spline-Filter (Glättung) 
            elif (self.radio_sfilter.isChecked()):
                # Filtername
                filtername = 'Spline-Filter'

                # Dateiendung festlegen
                dateiendung = '_sfilter'

                # Plott-Überschrift festlegen
                datenTitelFilter = 'Filter: Spline-Filter'

                # Filter S-Filter anwenden
                messdatenFilter = spline_filter(messdatenRaw, order=3)
            elif (self.radio_lfilter.isChecked()):
                # Filtername
                filtername = 'L-Filter'
            else:
                self.log("Schwerwiegender Fehler")

            self.log(filtername+" wird angewandt")

            # Matrix Größe
            zeilen = int(dateiInfo[1])
            spalten = int(dateiInfo[2])
            
            # Plotüberschriften festlegen
            datenTitel = dateiname
            datenTitelarrayDiff = 'Große Abweichungen'

            # Matrix / Messdaten plotten

            # Figure erzeugen, 3x2 Grid
            f, axs = plt.subplots(3, 2, figsize=(10,20), sharey=True)

            # Abstand zu Plots halten
            #f.tight_layout()
            f.subplots_adjust(hspace=0.45, wspace=0.3)

            # 4 x,y-Achsen erzeugen
            ax1 = axs[0, 0]; ax2 = axs[0, 1]
            ax3 = axs[1, 0]; ax4 = axs[1, 1]
            ax5 = axs[2, 0]; ax6 = axs[2, 1]

            # Hauptueberschrift
            f.suptitle(datenTitel, fontsize=18)

            # Rohdaten darstellen
            axs[0, 0].matshow(messdatenRaw)

            # Ueberschrift / Achsenbeschriftung festlegen
            axs[0, 0].set_title("Messdaten", fontsize=11)
            ax1.set_xlabel('x / µm')
            ax1.set_ylabel('y / µm')

            # erste und letzte Einträge korrigieren
            data00 = messdatenRaw[0][0]; data01 = messdatenRaw[0][-1]
            data10 = messdatenRaw[-1][0]; data11 = messdatenRaw[-1][-1]

            messdatenFilter[0][0] = data00; messdatenFilter[0][-1] = data01
            messdatenFilter[-1][0] = data10; messdatenFilter[-1][-1] = data11

            # Medfilt-Daten darstellen
            ax2.matshow(messdatenFilter)

            # Ueberschrift / Achsenbeschriftung festlegen
            ax2.set_title(datenTitelFilter, fontsize=11)
            ax2.set_xlabel('x / µm')
            ax2.set_ylabel('y / µm') 

            # Werte in der Matrix, die sich unterscheiden
            messdaten_diff = np.equal(messdatenRaw, messdatenFilter)
            
            #colormap = colors.ListedColormap(["red","green"])
            #cmap = ListedColormap(['white', 'black'])

            # Werte anzeigen
            ax3.matshow(messdaten_diff)#, cmap=cmap)

            # Ueberschrift / Achsenbeschriftung festlegen
            ax3.set_title('Geänderte Messwerte', fontsize=11)
            ax3.set_xlabel('x')
            ax3.set_ylabel('y')

            # Stärke der Abweichung berechnen
            array_difference = messdatenRaw - messdatenFilter 

            # Werte anzeigen
            ax4.matshow(array_difference)

            # Ueberschrift / Achsenbeschriftung festlegen
            ax4.set_title(datenTitelarrayDiff, fontsize=11)
            ax4.set_xlabel('x / µm')
            ax4.set_ylabel('y / µm')

            # 2x2 Matrix in 1D umwandeln 
            array_flat = array_difference.flatten() 

            # sortiertes array 
            sorted_index_array = np.argsort(array_flat) 
            
            # sortiertes array 
            sorted_array = array_flat[sorted_index_array] 

            n = 5

            # n größte Werte finden 
            rslt = sorted_array[-n : ] 
            rslt_min = sorted_array[ : -n] 
            
            # n große Listen erstellen
            num = [None] * n
            
            posx = [None] * n; posy = [None] * n

            # Matrix auf 3 Nachkommastellen runden
            diff_stringList = np.round(array_difference, 3)

            # Wert-Position in Matrix ermitteln
            def getPos(z, value, list):
                for i in range(0, zeilen):
                    for j in range(0, spalten):
                        if not (list[i][j] == 0.0):
                            posx[z] = j
                            posy[z] = i

            # Wert in Matrix suchen, dann Position bestimmen                
            for i in range(0,n):
                num[i] = '%.3f'%rslt[i]

                equal = diff_stringList == float(num[i])
                drop = np.where(diff_stringList == float(num[i]), diff_stringList, 0)

                getPos(i, num[i], drop)

            # Kreis um Position zeichnen
            for i in range(0,n):
                ax4.scatter(posx[i], posy[i] , s=400, facecolor='none', edgecolors='white')

            # große Abweichungen anzeigen
            for i in range(0,n):
                # Label festlegen
                label = f"({num[i]})"

                # Plott Konfiguration
                ax4.annotate(label, 
                            (posx[i], posy[i]),
                            textcoords="offset points", # Text positionierung
                            color='white', # Text Farbe
                            xytext=(0,15), # Distanz von Text zu Punkt (x,y)
                            ha='center') # Horizontalausrichtung (left, right oder center)
                
            # eigene Surfaceplots erstellen
            x = np.arange(-zeilen/2, zeilen/2, 1)
            y = np.arange(-spalten/2, spalten/2, 1)

            x, y = np.meshgrid(x, x)

            # z Daten in neues 2D-Array schreiben
            z = []
            for i in range(0, zeilen):
                sub = []
                for j in range(0, spalten):
                    sub.append(messdatenRaw[i][j])
                z.append(sub)

            z = np.array(z)

            # Messwerte anzeigen
            ax7 = f.add_subplot(3, 2, 5, projection='3d')
            
            ax7.plot_surface(x, y, z, cmap=cm.cool, linewidth=0, antialiased=False)

            # Ueberschrift / Achsenbeschriftung festlegen
            ax7.set_title("Messdaten", fontsize=11)
            ax7.set_xlabel('x / µm')
            ax7.set_ylabel('y / µm')
            ax7.set_zlabel('z / µm')

            # Filter Werte anzeigen
            ax8 = f.add_subplot(3, 2, 6, projection='3d')
            
            z = messdatenFilter
            ax8.plot_surface(x, y, z, cmap=cm.cool, linewidth=0, antialiased=False)

            # Ueberschrift / Achsenbeschriftung festlegen
            ax8.set_title(datenTitelFilter, fontsize=11)
            ax8.set_xlabel('x / µm')
            ax8.set_ylabel('y / µm')
            ax8.set_zlabel('z / µm')

            # Achse 5 und 6 ausblenden
            ax5.axis('off')
            ax6.axis('off')

            # Add a color bar which maps values to colors.
            #fig.colorbar(surf, shrink=1, aspect=5)

            # pfad = datei.replace(dateiname,'')

            # Speicherung Plott (png)
            if(plotSpeichern):
                print("png-Datei wird gerade gespeichert")
                plt.savefig(dateiname+dateiendung+'.png')
            
            # Speicherung Daten (csv)
            if(datenSpeichern):
                print("csv-Datei wird gerade gespeichert")

                # Header nach Vorgabe erstellen
                matrixInfo = 'Matrixgröße: ' + str(zeilen)+'x'+str(spalten)
                pixelInfo = 'Pixelgröße: ' + str(pixelgroesse) #+ ' ' + str(einheit)
                
                # csv-datei encoding: iso-8859-1
                # mit charset-detector bestimmt 

                # Neue csv-Datei öffnen
                with open(dateiname+dateiendung+'.csv', 'w', newline='', encoding='iso-8859-1') as file:
                    writer = csv.writer(file, delimiter=',')#, quoting=csv.QUOTE_NONE)

                    # Daten in csv-Datei schreiben
                    writer.writerow([matrixInfo])
                    writer.writerow([pixelInfo])

                    writer.writerows(messdatenFilter)

            # Plott anzeigen
            plt.show()
        else:
            # Fehlermeldung, keine Datei eingelesen
            self.log("Bitte Datei einlesen!")
        
    # Filterfunktion, L-Filter    
    def lfilter(self, datei):
        t = np.linspace(-1, 1, 201)
        x = (np.sin(2*np.pi*0.75*t*(1-t) + 2.1) +
            0.1*np.sin(2*np.pi*1.25*t + 1) +
            0.18*np.cos(2*np.pi*3.85*t))
        xn = x + np.random.randn(len(t)) * 0.08
        b, a = signal.butter(3, 0.05)

        zi = signal.lfilter_zi(b, a)
        z, _ = signal.lfilter(b, a, xn, zi=zi*xn[0])

        z2, _ = signal.lfilter(b, a, z, zi=zi*z[0])
        y = signal.filtfilt(b, a, xn)

        plt.figure
        plt.plot(t, xn, 'b', alpha=0.75)
        plt.plot(t, z, 'r--', t, z2, 'r', t, y, 'k')
        #plt.legend(('noisy signal', 'lfilter, once', 'lfilter, twice',
        #            'filtfilt'), loc='best')
        plt.grid(True)
        plt.show()

    # Dateiinformationen auslesen
    def ausleseDateiinfo(self, datei):
        global dateiInfo; global solldaten
        global pixelgroesse

        # Datei öffnen
        with open(datei, 'r', encoding='iso-8859-1') as f:
            # erste zwei Zeilen einlesen
            head = [next(f) for x in range(2)]

        dateiname = datei.split('/')[-1]

        # Matrixgröße
        matrixgroesse = head[0]

        # Zeilen- / Spaltengröße ausschneiden
        zeilen = (matrixgroesse.split(' ')[1]).split('x')[0]
        spalten = (matrixgroesse.split(' ')[1]).split('x')[1]

        dateiInfo[0] = dateiname

        dateiInfo[1] = zeilen 
        dateiInfo[2] = spalten

        # Pixelgröße
        pixelgroesse = head[1].split(' ')[1]

        # Einheit der Pixelgröße
        einheit = head[1].split(' ')[2]

        # Pfad ermitteln
        pfad = datei.replace(dateiname,'')

        # Solldaten ermitteln
        ordner = re.search('BigData/(.*)/', pfad)

        solldaten = pfad + "/Solldaten_" + ordner.group(1) + ".csv"
        solldatenDatei = "Solldaten_" + ordner.group(1) + ".csv"

        self.log("Datei erfolgreich eingelesen")
        self.log("Bitte Filter und Export-Optionen wählen")

        # Funktion zum anzeigen der ermittelten Werten aufrufen
        # Die Werte sind dabei gleichzeitig die Parameter
        self.fileInfo.setText("Dateiname: "+dateiname+"\n"+"Solldaten: "+solldatenDatei+"\n"+matrixgroesse+head[1])

    # Datenimport / Datei auswählen    
    def browsefiles(self):
        global dateiauswahl
        global neuauswahl
        global startDir

        # getOpenFileName<s> für mehrere Dateien
        # Dialog öffnen, nur csv-Dateien auswählbar
        csvDatei = QFileDialog.getOpenFileName(self, 'Messwerte einlesen', startDir, "CSV-Dateien (*.csv)")

        if not (csvDatei[0] == ''):
            dateiauswahl = csvDatei[0]
            pngDatei = dateiauswahl[:-4]+".png"

            self.filename.setText(dateiauswahl) 
            
            # Messdaten-Plott öffnen
            bild = Image.open(pngDatei)

            # neues Bild erstellen, auf Labelgröße anpassen
            new_image = bild.resize((431, 291))

            # neues Bild speichern
            new_image.save('temp.png')
            
            # Pixmap erstellen und anzeigen
            pixmap = QPixmap('temp.png')
            
            self.plot.setPixmap(pixmap)

            # Wenn neue Datei eingelesen, Rauheit 0 setzen
            if (neuauswahl == 1):
                #self.rauheit()
                self.mittenrauwertSa.setText("Sa = nicht berechnet")
                self.quadratrauwertSq.setText("Sq = nicht berechnet")

            # ausgewählte Datei an Funktion ausleseDateiinfo übergeben
            MainWindow.ausleseDateiinfo(self, dateiauswahl)
        else:
            return 0
    
    # Hauptfunktion
    def main(self):
        global dateiauswahl; dateiInfo
        global plotSpeichern; global datenSpeichern
        
        # Button für Dateibrowser
        self.browse.clicked.connect(self.browsefiles)

        # Button zum Entpacken
        self.entpacken.clicked.connect(self.entzip)

        # Häkchen für Plot und Daten speicherung
        self.savePlot.clicked.connect(self.plotExport)
        self.saveData.clicked.connect(self.datenExport)

        # Button um Rauheit zu berechnen
        self.ra.clicked.connect(self.rauheit)

        # Lambda functions are used when you need a function for a short period of time.
        # Button um Daten zu filtern
        self.dataFilter.clicked.connect(lambda: self.filter(dateiauswahl))

# Anwendung erzeugen
app = QtWidgets.QApplication(sys.argv)

# Fenster erzeugen
w = MainWindow()
# Fenster anzeigen/starten
w.show()

# Programm beenden
sys.exit(app.exec_())
