Raphael.fn.pieChart = function (cx, cy, r, values, labels, stroke) {
    var paper = this,
        rad = Math.PI / 180,
        chart = this.set();
    function sector(cx, cy, r, startAngle, endAngle, params) {
        var x1 = cx + r * Math.cos(-startAngle * rad),
            x2 = cx + r * Math.cos(-endAngle * rad),
            y1 = cy + r * Math.sin(-startAngle * rad),
            y2 = cy + r * Math.sin(-endAngle * rad);
        return paper.path(["M", cx, cy, "L", x1, y1, "A", r, r, 0, +(endAngle - startAngle > 180), 0, x2, y2, "z"]).attr(params);
    }
    var angle = 0,
        total = 0,
        start = 0,
        process = function (j) {
            var value = values[j],
                angleplus = 360 * value / total,
                popangle = angle + (angleplus / 2),
                color = Raphael.hsb(start, .75, 1),
                ms = 500,
                delta = 30,
                bcolor = Raphael.hsb(start, 1, 1),
                p = sector(cx, cy, r, angle, angle + angleplus, {fill: "90-" + bcolor + "-" + color, stroke: stroke, "stroke-width": 3}) //,
                //txt = paper.text(cx + (r + delta + 55) * Math.cos(-popangle * rad), cy + (r + delta + 25) * Math.sin(-popangle * rad), labels[j]).attr({fill: bcolor, stroke: "none", opacity: 0, "font-size": 20});
            p.mouseover(function () {
                p.stop().animate({transform: "s1.1 1.1 " + cx + " " + cy}, ms, "elastic");
                //txt.stop().animate({opacity: 1}, ms, "elastic");
            }).mouseout(function () {
                p.stop().animate({transform: ""}, ms, "elastic");
                //txt.stop().animate({opacity: 0}, ms);
            });
            angle += angleplus;
            chart.push(p);
            //chart.push(txt);
            start += .1;
        };
    
    function update_values() {
        for (var i = 0, ii = values.length; i < ii; i++) {
            total += values[i];
        }
        for (i = 0; i < ii; i++) {
            process(i);
        }
        return chart;
    }
    update_values();
};

/*
var r = Raphael("holder");
r.customAttributes.segment = function (x, y, r, a1, a2) {
    var flag = (a2 - a1) > 180,
        clr = (a2 - a1) / 360;
    a1 = (a1 % 360) * Math.PI / 180;
    a2 = (a2 % 360) * Math.PI / 180;
    return {
        path: [["M", x, y], ["l", r * Math.cos(a1), r * Math.sin(a1)], ["A", r, r, 0, +flag, 1, x + r * Math.cos(a2), y + r * Math.sin(a2)], ["z"]],
        fill: "hsb(" + clr + ", .75, .8)"
    };
};

points = [10, 20, 15];
total = 45;
start = 0;
paths = [];
for(i=0; i<=2; i++) {
  size = 360 / total * points[i];
  var slice = r.path();
  slice.attr({segment: [250, 250, 200, start, start + size], stroke: "#000", title: "Slice "+i});
  paths.push(slice);
  start += size;
}
*/

/*
newPoints = [5, 20, 20];
start = 0;
for(i=0; i<=2; i++) {
  size = 360 / total * newPoints[i];
  paths[i].animate({segment: [250, 250, 200, start, start + size]}, 800);
  paths[i].angle = start - size / 2;
  start += size;
}
*/
