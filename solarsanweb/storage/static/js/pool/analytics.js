
//
// Storage Pools Analytics
// - using Cubism and/or NVD3
//

pool_analytics = {
    pool: null,
    cube_url: null,

    small_stats: function() {
        var pthis = this;
        var step = +cubism.option("step", 3e5);
        var context = cubism.context()
            .step(step)
            .size(780);

        if (!pthis.pool)
            console.log('No pool specified');
        var pool_name = pthis.pool;

        if (!pthis.cube_url)
            pthis.cube_url = "http://localhost:1081";

        var cube = context.cube(pthis.cube_url);

        /*
        // Add top and bottom axes to display the time.
        d3.select("#graph_iops").selectAll(".axis")
            .data(["top", "bottom"])
        .enter().append("div")
        .attr("class", function(d) { return d + " axis"; })
            .each(function(d) { d3.select(this).call(context.axis().ticks(12).orient(d)); });

        // Add a mouseover rule.
        d3.select("#graph_iops").append("div")
            .attr("class", "rule")
            .call(context.rule());
        */

        d3.select("#graph_iops")
            .selectAll(".horizon")
                .data([
                    {title: "iops", metric: cube.metric('sum(pool_iostat(iops_read + iops_write).eq(pool,"'+pool_name+'"))')},
                    {title: "bandwidth", metric: cube.metric('sum(pool_iostat(bandwidth_read + bandwidth_write).eq(pool,"'+pool_name+'"))').multiply(-1)}
                    //{title: "iops", metric: cube.metric('sum(pool_iostat(iops_read + iops_write).eq(pool,"{{ object.name }}"))').divide(step)},
                    //{title: "bandwidth", metric: cube.metric('sum(pool_iostat(bandwidth_read + bandwidth_write).eq(pool,"{{ object.name }}"))').divide(step)},
                ])
            .enter().append("div")
                .attr("class", "horizon")
            .call(context.horizon()
                .title(function(d) { return d.title; })
                .metric(function(d) { return d.metric; })
                .height(20)
        );
    },  // end:small_stats

    graph: function(selector, chart_name, data) {
        var pthis = this;
        // Wrapping in nv.addGraph allows for '0 timeout render', stors rendered charts in nv.graphs, and may do more in the future... it's NOT required
        return nv.addGraph(function() {
            //if (nv.graphs.length)
                //nv.graphs[0] = chart;
                //var chart = nv.graphs[0];
            //else
                var chart = nv.models.stackedAreaChart().clipEdge(true);
                //var chart = nv.models.lineChart();

            // chart sub-models (ie. xAxis, yAxis, etc) when accessed directly, return themselves, not the partent chart, so need to chain separately
            chart.xAxis
                .axisLabel('when')
                .tickSize(5,5,5)
                //.tickFormat(function(d) { return d3.time.format('%x')(new Date(d)) });
                //.tickPadding(20)
                .tickFormat(function(d) { return d3.time.format('%m/%e %I:%M%p')(new Date(d)) });
                //.rotateLabels(-45);

            chart.yAxis
                .axisLabel(chart_name)
                .tickFormat(d3.format(',.3s'));

            function eat_data(data) {
                if (!data) return false;

                data = data.map(function(series) {
                    series.values = series.values.map(function(d) {
                        return { x: d[0], y: d[1] }
                    });
                    return series;
                });

                d3.select('#chart svg')
                    .datum(data)
                    .transition().duration(1000).call(chart);
            }

            eat_data(data);

            //TODO: Figure out a good way to do this automatically
            nv.utils.windowResize(chart.update);

            return chart;
        });
    }  // graph:end
};

