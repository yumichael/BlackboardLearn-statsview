// JavaScript source code
// var grade exists
var totalPoints = info['total_points'];
var metric = 'Quiz 1';
var group = 'Tut 01';
var plotID = 'the-plot';
var plotData = [{
    type: 'histogram',
    x: [],
    xbins: {
        start: 0,
        end: 1,
        size: 1
    },
    autobinx: false,
    hoverinfo: 'skip'
}];
var layout = {
    title: 'Choose a section and a test',
    xaxis: {
        title: 'Grade',
        range: [0, 1],
        tick0: 0,
        dtick: 1
    },
    yaxis: {
        range: [0, 18]
    },
    shapes: [{
        'line': {
            'color': '#0099FF', 'dash': 'solid', 'width': 1
        },
        'type': 'line',
        'x0': 0,
        'x1': 0,
        'xref': 'x',
        'y0': -0.09,
        'y1': 1,
        'yref': 'paper'
    }],
    annotations: [{
        x: 0,
        y: -.1,
        xref: 'x',
        yref: 'paper',
        text: '',
        showarrow: true,
        arrowhead: 7,
        ax: 1,
        ay: 1,
        axref: 'paper',
        ayref: 'paper'
    }]
};

function makePlot() {
    Plotly.newPlot(plotID, plotData, layout);
}

function refreshPlot() {
    layout.title = 'Missing data';
    layout.xaxis.range = [0, 1];
    plotData[0].x = [];
    plotData[0].xbins.end = 1;
    plotData[0].xbins.size = 1;
    layout.xaxis.dtick = 1;
    Plotly.redraw(plotID);

    layout.title = metric + ', ' + group;
    layout.xaxis.range = [-totalPoints[metric] / 40, totalPoints[metric] * 1.025];
    plotData[0].x = grades[metric][group];
    plotData[0].xbins.end = totalPoints[metric] * 1.025;
    plotData[0].xbins.size = totalPoints[metric] / 20;
    layout.xaxis.dtick = totalPoints[metric] / 10;
    layout.shapes[0].x0 = mean(grades[metric][group]);
    layout.shapes[0].x1 = mean(grades[metric][group]);
    layout.annotations[0].x = mean(grades[metric][group]);
    layout.annotations[0].text = "Mean = " + mean(grades[metric][group]).toFixed(1);
    Plotly.redraw(plotID);
}

$(document).ready(function () {
    makePlot();
    $(".click-metric[value='" + metric + "']").addClass('active');
    $(".click-group[value='" + group + "']").addClass('active');
    refreshPlot();
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

// Stats functions
function mean(numbers) {
    // mean of [3, 5, 4, 4, 1, 1, 2, 3] is 2.875
    var total = 0,
        i;
    for (i = 0; i < numbers.length; i += 1) {
        total += numbers[i];
    }
    return total / numbers.length;
}