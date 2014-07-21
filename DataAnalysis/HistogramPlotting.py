
from statsmodels.discrete.discrete_model import L1BinaryResults
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import Plotting as pl
import Resampling as rs
import io
from PIL import Image
class HistogramPlot():
    """ The is the class for histrogram type of plots """
    EWMAHeading = "Predicted usage - EWMA"
    EQHeading = "Predicted usage - Equal"
    coloredFirst = '#99FF33'
    coloredSecond = '#6699CC'
    def __init__(self):
        """Stuff that must be initialized when this class is created"""

    def doHistogramPlotting(self,dataFrameIn,dataFrameExtra,amountOfWeight = 1,freqVal='1min',min_periodsVal=1,
                               Title="YourTitle",YLabel="Y",XLabel="Timestamp",fileType="png",typeWeight = "EWMA"):
        """Specify the dateFrame that you want to plotted against its EMWA or rolling_mean using a histogram plot
        you require the parameters to shape the plot.

        The whole idea of this is to not aggregate but to do sums, this will possibly plot summations
        of readings, which is basically comparing the current to the expected sum of usage in that interval

        fileType: This is .png or .bmp ect which the self.histPlotDouble will produce for this method to return
        freqVal: this is the down sampling to make the intervals cover a large section of the data
        min_periodsVal: This is good to default to 1 if you using summations

        Return: This will attempt to return the file that stores the figured for the plot
        """
        dateFrameWeighted = None
        LegendToSend =""
        dfIN = dataFrameIn
        dfWeighted = dataFrameExtra

        dfIN = rs.Resampling().downsample_data_frame(data_frame=dfIN, freq=freqVal, method="sum")
        #this will be fixed, was thinking 10 x freq to down sample further, i want to keep consistency
        dfIN = rs.Resampling().downsample_data_frame(data_frame=dfIN,freq="10min",method="mean")


        #dfWeighted = pd.DataFrame(dfWeighted,columns=("reading",))
        dfWeighted = rs.Resampling().downsample_data_frame(data_frame=dfWeighted,freq=freqVal,method="sum")


        ## check the weight in order to decide on the weighting system used
        if (typeWeight == "EWMA"):
            dfWeighted = pl.Plotter().ewma_resampling(data_frame=dfWeighted,weight =amountOfWeight,
                                                             freq="10min",min_periods=min_periodsVal)
            LegendToSend= self.EWMAHeading
        else:
            dfWeighted = pl.Plotter().equal_weight_moving_average(data_frame=dfWeighted,
                                                                      freq="10min",min_periods=min_periodsVal)
            LegendToSend= self.EQHeading

        return self.histPlotDouble(dataFrameOriginal=dfIN,dataFrameWeighted=dfWeighted,
                            LegendLabelWeighted=LegendToSend,Title=Title,YLabel=YLabel,
                             XLabel=XLabel,fileType=fileType)


    def histPlotDouble(self,dataFrameOriginal,dataFrameWeighted,LegendLabelOriginal="Current reading",
                                     LegendLabelWeighted="weighted plot",Title="YourTitle",YLabel="Y",XLabel="Timestamp",
                                     fileType="png"):
        """Specify the dataFrame that you want to plot, a weighted vs actual readings currently

        Title: The title for the plot : "THE BEST PLOT EVER"
        YLabel: The label for the y axis : reading(kWh)
        XLabel: The label for the x axis : Time Stamp
        fileType: The type of image you looking for
        Labels: These are for your plots so you can have a lengend which is useful

        Return: a image generated by the figure and combination of the ByteIO
        """

        FileToReturn = None
        canSave = False
        if (len(LegendLabelOriginal) <= 0):
                LegendLabelOriginal="current readings"
        if (len(LegendLabelWeighted) <= 0):
                LegendLabelWeighted="weighted readings"
        if (len(XLabel) == 0):
            XLabel = "X"
        if (len(YLabel) == 0):
            YLabel = "Y"
        if (len(Title) == 0):
            Title = "The plot"

        if (not(fileType.__eq__("bmp") or fileType.__eq__("png") or fileType.__eq__("jpg"))):
            fileType = "png"

        #print(dataFrameOriginal)
        dataFrameWeighted = pd.DataFrame(dataFrameWeighted,columns=("reading",))
        mino,maxo = rs.Resampling().get_max_value_in_frame(dataFrameOriginal)
        minw,maxw = rs.Resampling().get_max_value_in_frame(dataFrameWeighted)  # the issue is indexing in a weighted df

        maxv = max(maxw,maxo) +5
        minv = min(minw,mino) -1


        if (maxw>maxo):
            ori = dataFrameOriginal.reading.plot(label=LegendLabelOriginal,legend=LegendLabelOriginal,kind = "bar",color= self.coloredFirst)
            wei = dataFrameWeighted.reading.plot(label=LegendLabelWeighted,legend=LegendLabelWeighted,kind = "bar",color= self.coloredSecond,stacked=True)
        else:
            wei = dataFrameWeighted.reading.plot(label=LegendLabelWeighted,legend=LegendLabelWeighted,kind = "bar",color= self.coloredFirst)
            ori = dataFrameOriginal.reading.plot(label=LegendLabelOriginal,legend=LegendLabelOriginal,kind = "bar",color= self.coloredSecond,stacked=True)


        plt.legend()
        plt.ylim([minv,maxv])
        plt.ylabel(YLabel)
        plt.xlabel(XLabel)
        plt.title(Title)
        buf = io.BytesIO()
        plt.savefig(buf, format = fileType,bbox_inches ="tight",dpi = 300,facecolor ="w",edgecolor="g")
        buf.seek(0)
        im = Image.open(buf)

        # possibly should use save fig
        return im


    def findXtickers(self,dataFrameIN):
        """
        This is the method that will get your xtickers for figures
        This because using the plot function from plt is restrictive, especially when it comes to subplotting
        and bar graphs!!!! aka hist!!!!

        Return: This will return an pd.timestamp array for you x-axis
        """
        timestarted = (dataFrameIN.ix[0].name)
        nextinline = (dataFrameIN.ix[1].name)
        timeeended =   (dataFrameIN.ix[dataFrameIN.__len__()-1].name)
        xtickers = []

        xtickers.append(timestarted)
        xSingleDiff = nextinline - timestarted
        xTotalDiff = timeeended - timestarted
        totalTickers = (xTotalDiff.seconds/60)/(xSingleDiff.seconds/60)

        changingTime = timestarted
        for x in range(1, totalTickers):
            changingTime = changingTime + xSingleDiff
            xtickers.append(changingTime)

        return xtickers

