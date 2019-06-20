define(['d3'], function(d3){
    /**
    *
    * D3 bar chart with negative values
    * @author Christoph Franke
    */
    class BarChart {

        /**
        * create the map and show it inside the HTMLElement with the given id
        *
        * @param {Object} options
        * @param {string} options.el            the HTMLElement to render the chart into
        * @param {boolean} [options.width]
        * @param {boolean} [options.height]
        *
        */
        constructor(options){
            var _this = this,
                margin = {top: 20, right: 30, bottom: 40, left: 30},
                width = options.width || options.el.offsetWidth - margin.left - margin.right;
            this.height = options.height || options.el.offsetHeight - margin.top - margin.bottom;

            this.x = d3.scale.ordinal()
                .rangeRoundBands([0, width], 0.1);

            this.y = d3.scale.linear()
                .range([0, this.height]);

            this.xAxis = d3.svg.axis()
                .scale(this.x)
                .orient("bottom")
                .tickSize(0)
                .tickPadding(6);

            this.zeroAxis = d3.svg.axis()
                .scale(this.x)
                .orient("bottom")
                .tickFormat("")
                .tickSize(0);

            this.yAxis = d3.svg.axis()
                .scale(this.y)
                .orient("left");

            this.svg = d3.select(options.el).append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", this.height + margin.top + margin.bottom)
              .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
        }

        draw(data){
            var _this = this;
            this.x.domain(data.map(function(d) { return d.name; }));
            this.y.domain(d3.extent(data, function(d) { return -d.value; })).nice();

            this.svg.selectAll(".bar")
                .data(data)
              .enter().append("rect")
                .attr("class", function(d) { return "bar bar--" + (d.value < 0 ? "negative" : "positive"); })
                .attr("x", function(d) { return _this.x(d.name); })
                .attr("y", function(d) { return _this.y(Math.min(0, -d.value)); })
                .attr("height", function(d) { return Math.abs(_this.y(d.value) - _this.y(0)); })
                .attr("width", this.x.rangeBand())
                .style("fill", function(d) { return d.color || 'grey'; });

            this.svg.selectAll(".value")
              .data(data)
              .enter().append("text")
                .attr("x", function(d) { return _this.x(d.name) + _this.x.rangeBand() / 2; })
                .attr("y", function(d) { return _this.y(-d.value); })
                .attr("dy", ".35em")
                .text(function(d) { return d.text || d.value });

                // zero line
            this.svg.append("g")
                .attr("class", "x zero")
                .attr("transform", "translate(0," + this.y(0) + ")")
                .call(this.zeroAxis)
              .select('path')
                .style("stroke", '#000');

            this.svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + this.height + ")")
                .call(this.xAxis);

            //this.svg.append("g")
                //.attr("class", "y axis")
                //.attr("transform", "translate(" + this.x(0) + ",0)")
                //.call(this.yAxis);
        }
    };

    return BarChart;
});
