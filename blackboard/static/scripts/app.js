// JavaScript source code
// var grade exists
var totalPoints = info['total_points'];
var metric = 'Quiz 1';
var group = 'Tut 01';
var plotID = 'the-plot';
var plotData = [{
    x: grades[metric][group],
    type: 'histogram',
    xbins: {
        start: -totalPoints[metric] / 40,
        end: totalPoints[metric] * 1.025,
        size: totalPoints[metric] / 20
    },
    autobinx: false,
    hoverinfo: 'skip'
}];
var layout = {
    title: metric + ', ' + group,
    xaxis: {
        title: 'Grade',
        range: [-totalPoints[metric] / 40, totalPoints[metric] * 1.025],
        tick0: 0,
        dtick: totalPoints[metric] / 20
    },
    yaxis: {
        range: [0, 12]
    }
};

function makePlot() {
    Plotly.newPlot(plotID, plotData, layout);
}

function refreshPlot() {
    layout.title = metric + ', ' + group;
    layout.xaxis.range = [-totalPoints[metric] / 40, totalPoints[metric] * 1.025];
    plotData[0].x = grades[metric][group];
    plotData[0].xbins.end = totalPoints[metric] * 1.025;
    plotData[0].xbins.size = totalPoints[metric] / 20;
    layout.xaxis.dtick = totalPoints[metric] / 20;
    //Plotly.purge(plotID);
    //$('#' + plotID).empty();
    Plotly.redraw(plotID);
}

$(document).ready(function () {
    makePlot();
    $('.click-metric').click(function () {
        $('.click-metric.active').removeClass('active');
        $(this).addClass('active');
        metric = $(this).val();
        refreshPlot();
    })
    $('.click-group').click(function () {
        $('.click-group.active').removeClass('active');
        $(this).addClass('active');
        group = $(this).val();
        refreshPlot();
    })
});