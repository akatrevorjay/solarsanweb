
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
        console.log("graphs_update_ajax_callback");

        for (var g in series) {
            if (graphs[g] && $('#'+g).hasClass('ajax')) {
                if (graphs[g]['type']=='pie' || graphs[g]['type']=='pie2') {
                    graphs[g]['values'] = series[g]['values'];
                } else if (graphs[g]['type']=='analytics') {
                    if (!graphs[g]['values'])
                        graphs[g]['values'] = [];
                    if (graphs[g]['values'].length >= 10)
                        graphs[g]['values'].shift();
                    graphs[g]['values'].push( (series[g]['values'][0] + series[g]['values'][1]) );
                } else if (graphs[g]['type']=='line') {
                    if (!graphs[g]['values'])
                        graphs[g]['values'] = [];
                    for (var i in series[g]['values']) {
                        if (!graphs[g]['values'][i])
                            graphs[g]['values'][i] = [];
                        if (graphs[g]['values'][i].length >= 10)
                            graphs[g]['values'][i].shift();
                        graphs[g]['values'][i].push(series[g]['values'][i]);
                    }
                }
                graph_redraw(g);
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
    
    function graph_redraw(g) {
        if (graphs[g]['type']=='pie') {
            if (!graphs[g]['r'])
                graphs[g]['r'] = Raphael(g);
            else
                graphs[g]['r'].clear();

            //graphs[g]['r'].text(graphs[g]['width'], graphs[g]['radius'], graphs[g]['title']).attr({ font : "12px sans-serif" });
            graphs[g]['pie'] = graphs[g]['r'].piechart(graphs[g]['width'], graphs[g]['height'], graphs[g]['radius'], graphs[g]['values'], graphs[g]['opts'] );

            graphs[g]['pie'].hover(graphs[g]['hover'], graphs[g]['unhover']);
            graphs[g]['pie'].click(graphs[g]['click']);
        } else if (graphs[g]['type']=='pie2') {
            if (!graphs[g]['r'])
                graphs[g]['r'] = Raphael(g);
            else
                graphs[g]['r'].clear();

            if (!graphs[g]['pie']) {
                graphs[g]['r'].customAttributes.segment = function (x, y, r, a1, a2) {
                    var flag = (a2 - a1) > 180,
                        clr = (a2 - a1) / 360;
                    a1 = (a1 % 360) * Math.PI / 180;
                    a2 = (a2 % 360) * Math.PI / 180;
                    return {
                        path: [["M", x, y], ["l", r * Math.cos(a1), r * Math.sin(a1)], ["A", r, r, 0, +flag, 1, x + r * Math.cos(a2), y + r * Math.sin(a2)], ["z"]],
                        fill: "hsb(" + clr + ", .75, .8)"
                    };
                };
            }
            graphs[g]['pie'] = graphs[g]['r'].pieChart(graphs[g]['width'], graphs[g]['height'], graphs[g]['radius'], graphs[g]['values'], graphs[g]['legend'], "#000");
        } else if (graphs[g]['type']=='analytics') {
            if (!graphs[g]['r'])
                graphs[g]['r'] = Raphael(g, graphs[g]['width'], graphs[g]['height']);
            else
                graphs[g]['r'].clear();

            console.log("graph_redraw: "+g+" values: "+graphs[g]['values']);
            
            graphs[g]['labels'] = [];
            for (i in graphs[g]['values']) {
                graphs[g]['labels'].push(i);
            }
            graphs[g]['analytics'] = draw_analytics(g);
        } else if (graphs[g]['type']=='line') {
            if (!graphs[g]['r'])
                graphs[g]['r'] = Raphael(g, graphs[g]['width'], graphs[g]['height']);
            else
                graphs[g]['r'].clear();

            graphs[g]['lines'] = graphs[g]['r'].linechart(10, 0, graphs[g]['width'] - 10, graphs[g]['height'] - 10,
                //graphs[g]['values']
                [[0,1,2,3,4,5,6,7,8,9], [0,1,2,3,4,5,6,7,8,9]], [graphs[g]['values'][0], graphs[g]['values'][1]],
                //[[1, 2, 3, 4, 5, 6, 7, 8, 9],[3.5, 4.5, 5.5, 6.5, 7, 8]], [[12, 32, 23, 15, 17, 27, 22], [10, 20, 30, 25, 15, 28]],
                { nostroke: false, axis: "0 0 1 1", symbol: "circle", smooth: true }).hoverColumn(function () {
                    //this.tags = r.set();

                    //for (var i = 0, ii = this.y.length; i < ii; i++) {
                    //    this.tags.push(r.tag(this.x, this.y[i], this.values[i], 160, 10).insertBefore(this).attr([{ fill: "#fff" }, { fill: this.symbols[i].attr("fill") }]));
                    //}
                }, function () {
                    //this.tags && this.tags.remove();
                });

                graphs[g]['lines'].symbols.attr({ r: 6 });
                // lines.lines[0].animate({"stroke-width": 6}, 1000);
                // lines.symbols[0].attr({stroke: "#fff"});
                // lines.symbols[0][1].animate({fill: "#f00"}, 1000);


        }
    }








/*

$(function() {
    function MergeJSON(o, ob) {
        for(var z in ob) {
            o[z] = ob[z];
        }
        return o;
    }

    function graph_update_ajax_callback2(graph, timeout, series) {
        console.log("graph_update_ajax_callback: " + graph);
        var graph_plot = graphs[graph];

        if($("#" + graph).hasClass("ajax_graph_donut")) {
            graph_plot.setData(series);
        } else if($("#" + graph).hasClass("ajax_graph_line")) {
            graph_plot.setData(MergeJSON(graph_plot.getData(), series));
        }

        graph_plot.setupGrid();
        graph_plot.draw();
        //graph_plot.triggerRedrawOverlay();

        delete graph_plot

        if(timeout) {
            setTimeout(function() {
                graph_update_ajax(graph, timeout);
            }, timeout);
        }
    }

    function graph_update_ajax2(graph, timeout) {
        //console.log("graph_update_ajax: "+graph);
        $.ajax({
            type : "GET",
            url : "{% url solarsan.views.graph_stats %}",
            data : "graph=" + graph,
            dataType : 'json',
            success : function(ret) {
                graph_update_ajax_callback(graph, timeout, ret);
            }
        });
    }

    function graph_donut_hover(event, pos, obj) {
        if(!obj)
            return;
        percent = parsefloat(obj.series.percent).toFixed(2);
        $("#hover").html('<span style="font-weight: bold; color: ' + obj.series.color + '">' + obj.series.label + ' (' + percent + '%)</span>');
    }

    var raphaels = {};
    var graphs = {};
    var graphs_pie = {};

    function graph_update_ajax_callback(g, timeout, series) {
        console.log("graph_update_ajax_callback: " + g);

        var values = [], labels = [];
        $("#graph_utilization_data tr").each(function() {
            values.push(parseInt($("td", this).text(), 10));
            labels.push($("th", this).text());
        });
        //graphs["graph_utilization"].pieChart(150, 150, 50, values, labels, "#fff");

        var r = graphs[g];
        var legends = {
            legend : ["Free", "Used"]
        };

        graphs_pie[g] = r.piechart(320, 240, 100, [55, 20, 13, 32, 5, 1, 2, 10], legends);
        var pie = graphs_pie[g];

        pie.hover(graph_pie_hover, graph_pie_unhover);

        if(timeout) {
            setTimeout(function() {
                graph_update_ajax(graph, timeout);
            }, timeout);
        }
    }

    function graph_update_ajax(g, timeout) {
        //console.log("graph_update_ajax: "+g);
        $.ajax({
            type : "GET",
            url : "{% url solarsan.views.graph_stats %}",
            data : "graph=" + g,
            dataType : 'json',
            success : function(ret) {
                graph_update_ajax_callback(g, timeout, ret);
            }
        });
    }

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


    $(".ajax_graph_pie").each(function() {
        var g = $(this).attr('id');
        graphs[g] = Raphael(g);

        graphs[g].text(320, 100, "Utilization").attr({
            font : "12px sans-serif"
        });

        $("#" + g + "_data").hide();
        graph_update_ajax(g, 5000);
        delete g
    });
});

*/
    /*
     $(".ajax_graph_line").each( function() {
     graphs[$(this).attr("id")] = $.plot($(this),[], {
     lines: { show: true },
     points: { show: true },
     xaxis: { tickDecimals: 0, tickSize: 1 }
     });
     });

     graph_update_ajax(5000);

     $(".ajax_graph").each( function() {
     graph_update_ajax($(this).attr("id"), 5000);
     });
     */
