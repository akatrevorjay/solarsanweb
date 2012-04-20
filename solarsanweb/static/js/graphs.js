
function graph_pie_hover() {
    this.sector.stop();
    this.sector.scale(1.1, 1.1, this.cx, this.cy);

    if(this.label) {
        this.label[0].stop();
        this.label[0].attr({
            r : 7.5
        });
        this.label[1].attr({
            "font-weight" : 800
        });
    }
}

function graph_pie_unhover() {
    this.sector.animate({
        transform : 's1 1 ' + this.cx + ' ' + this.cy
    }, 500, "bounce");

    if(this.label) {
        this.label[0].animate({
            r : 5
        }, 500, "bounce");
        this.label[1].attr({
            "font-weight" : 400
        });
    }
}

function graph_pie_click() {
    
}

function graphs_update_ajax_callback(url, timeout, data, series) {
    //console.log("graphs_update_ajax_callback");
    for (var p in series) {
        for (var g in series[p]) {
            if (graphs[p][g] && $('#'+p+'__'+g).hasClass('ajax')) {
                if (graphs[p][g]['type']=='pie' || graphs[p][g]['type']=='pie2' || graphs[p][g]['type']=='line') {
                    //console.log('g='+g+' values='+series[p][g]['values']);
                    graphs[p][g]['values'] = series[p][g]['values'];
                }
                graph_redraw(p, g);
            }
        }
    }
    
    if (timeout)
        setTimeout(function() { graphs_update_ajax(url, timeout, data); }, timeout);
}

function graphs_update_ajax(url, timeout, data) {
    $.ajax({
        type: "GET",
        url: url,
        data: data,
        dataType: 'json',
        success: function(ret) { graphs_update_ajax_callback(url, timeout, data, ret); }
    });
}

function graph_redraw(p, g) {
    graph = graphs[p][g];
    
    if (graph['type']=='pie') {
        if (!graph['r'])
            graph['r'] = Raphael(p+'__'+g, graph['width']*2 +graph['legend_width'], graph['height']*2);
        else
            graph['r'].clear();

        //graph['r'].text(graph['width'], graph['radius'], graph['title']).attr({ font : "12px sans-serif" });
        graph['pie'] = graph['r'].piechart(graph['width'], graph['height'], graph['radius'], graph['values'], graph['opts'] );

        graph['pie'].hover(graph['hover'], graph['unhover']);
        graph['pie'].click(graph['click']);
    } else if (graph['type']=='line') {
        if (!graph['r'])
            graph['r'] = Raphael(p+'__'+g, graph['width'], graph['height']);
        else
            graph['r'].clear();

        graph['lines'] = graph['r'].linechart(50, 0, graph['width'] - 50, graph['height'] - 10,
            [[0,1,2,3,4,5,6,7,8,9], [0,1,2,3,4,5,6,7,8,9]], [graph['values'][0], graph['values'][1]],
            { nostroke: false, axis: "0 0 1 1", symbol: "circle", smooth: true }).hoverColumn(function () {
                this.tags = this.paper.set();

                for (var i = 0, ii = this.y.length; i < ii; i++) {
                    //this.symbols[i].animate({ 'stroke-width': 6 }, 500);
                    this.tags.push(this.paper.tag(this.x, this.y[i], this.values[i], 180, 10).insertBefore(this).attr([{ fill: "#fff" }, { fill: this.symbols[i].attr("fill") }]));
                }
            }, function () {
                this.tags && this.tags.remove();
            });

            graph['lines'].symbols.attr({ r: 6 });
            //graph['lines'].lines[0].animate({"stroke-width": 6}, 1000);
            //graph['lines'].symbols[0].attr({stroke: "#fff"});
            //graph['lines'].symbols[0][1].animate({fill: "#f00"}, 1000);
    }
    
    graphs[p][g] = graph;
    delete graph;
}

