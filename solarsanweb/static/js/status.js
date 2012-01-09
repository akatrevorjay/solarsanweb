
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
