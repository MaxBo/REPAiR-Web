define(['d3', 'd3-tip'], function(d3, d3tip){
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
        * @param {Integer} [options.width]
        * @param {Integer} [options.height]
        * @param {boolean} [options.showValues=true]
        * @param {boolean} [options.hideLabels=false]
        * @param {boolean} [options.grouped=false]
        *
        */
        constructor(options){
            var _this = this,
                margin = {};
            margin.left = (options.margin && options.margin.left != null) ? options.margin.left : 30;
            margin.right = (options.margin && options.margin.right != null) ? options.margin.right : 30;
            margin.bottom = (options.margin && options.margin.bottom != null) ? options.margin.bottom : 40;
            margin.top = (options.margin && options.margin.top != null) ? options.margin.top : 20;
            var width = options.width || options.el.offsetWidth - margin.left - margin.right;
            this.height = options.height || options.el.offsetHeight - margin.top - margin.bottom;
            this.showValues = options.showValues;
            this.grouped = (options.grouped != null) ? options.grouped : false;
            this.hideLabels = (options.hideLabels != null) ? options.hideLabels : false;

            this.x = d3.scale.ordinal();
            this.x0 = d3.scale.ordinal().rangeRoundBands([0, width], 0.1);

            if (!this.grouped)
                this.x.rangeRoundBands([0, width], 0.1);

            this.y = d3.scale.linear()
                .range([0, this.height]);

            this.xAxis = d3.svg.axis()
                .scale(this.x)
                .orient("bottom")
                .tickSize(0)
                .tickPadding(6);

            this.zeroAxis = d3.svg.axis()
                .scale((this.grouped) ? this.x0 : this.x)
                .orient("bottom")
                .tickFormat("")
                .tickSize(0);

            this.yAxis = d3.svg.axis()
                .scale(this.y)
                .orient("left");

            /* Initialize tooltip */
            this.tooltip = d3tip()
                .attr('class', 'd3-tip')
                .offset([-10,0]);

            this.tooltip.html(function(d) {
                var title = d.name,
                    value = d.text || d.value;
                if (d.group) title += ' <i>' + d.group + '</i>';
                return "<h1>" + title + "</h1>" + "<br>" + value;
            });

            this.svg = d3.select(options.el).append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", this.height + margin.top + margin.bottom)
                .call(this.tooltip)
              .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
        }

        draw(data){
            var _this = this, de;
            if (this.grouped){
                data.forEach(function(d) { d.values.forEach(function(d0) { d0.group = d.group; }) })
                this.x0.domain(data.map(function(d, i) { return d.group; }));
                this.x.domain(data[0].values.map(function(d, i) { return d.name || i; })).rangeRoundBands([0, this.x0.rangeBand()]);
                this.y.domain([
                    d3.min(data, function(group) { return d3.min(group.values, function(d) { return -d.value; }); }),
                    d3.max(data, function(group) { return d3.max(group.values, function(d) { return -d.value; }); })
                ]);
            }
            else {
                this.x.domain(data.map(function(d, i) { return d.name || i; }));
                this.y.domain(d3.extent(data, function(d) { return -d.value; })).nice();
            }

            if (this.grouped){
                var slice = this.svg.selectAll(".slice")
                  .data(data)
                  .enter().append("g")
                  .attr("class", "g")
                  .attr("transform",function(d) { return "translate(" + _this.x0(d.group) + ",0)"; });

                de = slice.selectAll("rect")
                    .data(function(d) { return d.values; })
            }
            else {
                de = this.svg.selectAll(".bar")
                    .data(data)
            }
            de.enter().append("rect")
              .attr("x", function(d, i) { return _this.x(d.name || i) + d.offset || 0; })
              .attr("y", function(d) { return _this.y(Math.min(0, -d.value)); })
              .attr("height", function(d) { return Math.abs(_this.y(d.value) - _this.y(0)); })
              .attr("width", this.x.rangeBand())
              .style("fill", function(d) { return d.color || 'grey'; })
              .on("mouseover", function(d) {
                  d3.select(this).style("fill", d3.rgb(d.color || 'grey').darker(2));
                  _this.tooltip.show(d, this);
              })
              .on("mouseout", function(d) {
                  d3.select(this).style("fill", d.color || 'grey');
                  _this.tooltip.hide(d, this);
              });

            if (!this.hideLabels){
                this.svg.selectAll(".value")
                  .data(data)
                  .enter().append("text")
                    .attr("x", function(d) { return _this.x(d.name) + d.offset || 0 + _this.x.rangeBand() / 2; })
                    .attr("y", function(d) { return _this.y(-d.value); })
                    .attr("dy", ".35em")
                    .text(function(d) { return (_this.showValues) ? d.text || d.value : ''});
            }
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
