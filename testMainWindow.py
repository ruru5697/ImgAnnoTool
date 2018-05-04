import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore,QtWidgets,QtGui
import matplotlib.pyplot as plt
import sys

class My_Main_window(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super(My_Main_window,self).__init__(parent)
        self.resize(800,659)
        self.menu=QtWidgets.QMenu('plot')
        self.menu_action=QtWidgets.QAction('plot',self.menu)
        self.menu.addAction(self.menu_action)
        self.menuBar().addMenu(self.menu)

        self.menu_action.triggered.connect(self.plot_)
        self.centralWidget().setLayout(QLayout=QtWidgets.QLayout())

    def plot_(self):
        plt.cla()
        fig=plt.figure()
        ax=fig.add_axes([0.1,0.1,0.8,0.8])
        ax.set_xlim([-1,6])
        ax.set_ylim([-1,6])
        ax.plot([0,1,2,3,4,5],'o--')
        canvas=FigureCanvas(fig)
        self.my_widget.setContentsMargins(canvas)

if __name__ == '__main__':
    app=QtWidgets.QApplication(sys.argv)
    main_window=My_Main_window()
    main_window.show()
    sys.exit(app.exec_())