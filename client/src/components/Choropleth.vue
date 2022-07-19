<template>
    <figure>
        <svg id="chart" :width="width" :height="height">

            <g id="zoomGroup">
                <path v-for="path in geojson.features"
                      :key="`${path.properties.area_level_label}-${path.properties.area_name}`"
                      :d="geopath(path)"
                      :fill="path.color"
                      @click="zoomAndEmitClick(path)"
                      @mouseover="populateTooltip($event, path)"
                      @mouseout="removeTooltip()">
                </path>
            </g>

        </svg>

        <div v-if="showTooltip"
             class="tooltipContainer"
             :class="{ activeTooltip: showTooltip}"
             :style="{top: tooltip.y, left: tooltip.x}">
            <slot name="tooltip" :row="tooltip.values">
                <p v-for="(value, key) in tooltip.values" :key="key">{{ key }}: {{ value }}</p>
            </slot>
        </div>
    </figure>
</template>

<script>
import {geoPath, geoMercator} from 'd3-geo';
// eslint-disable-next-line no-unused-vars
import {transition} from "d3-transition";
import {select} from "d3-selection";

export default {
    name: "Choropleth",
    props: {
        width: Number,
        height: Number,
        geojson: Object,
        plotData: Array,
        margin: {
            type: Object,
            default: function () {
                return {top: 20, bottom: 20, left: 20, right: 20}
            }
        },
        zoomedValue: Object,
    },
    data() {
        return {
            showTooltip: false,
            tooltip: {
                x: 0,
                y: 0,
                values: {}
            },
            zoomState: false,
        }
    },
    computed: {
        projection() {
            return geoMercator()
                .fitExtent([
                        [this.margin.left, this.margin.top],
                        [this.width - this.margin.right, this.height - this.margin.bottom]
                    ],
                    this.geojson)
                .precision(1)
        },
        geopath() {
            return geoPath().projection(this.projection)
        },
    },
    methods: {
        zoomAndEmitClick(path) {
            this.zoomState = !this.zoomState
            const g = select("#zoomGroup")

            if (this.zoomState) {
                let border
                if (Object.keys(path).length > 0) {
                    if (path.properties.area_level_label === "District") {
                        let province_id = path.properties.parent_area_id
                        border = this.geojson.features.find(item => item.properties.area_id === province_id)
                    } else {
                        border = path
                    }
                }

                let [[x0, y0], [x1, y1]] = this.geopath.bounds(border)

                let scale = Math.min(8, 0.9 / Math.max((x1 - x0) / this.width, (y1 - y0) / this.height))

                g.transition()
                    .duration(500)
                    .attr("transform",
                        `translate(${this.width / 2} ${this.height / 2})scale(${scale})translate(${-(x0 + x1) / 2} ${-(y0 + y1) / 2})`
                    )

                this.$emit('click', path)
            } else {
                g.transition().duration(400).attr("transform", `translate(0 0) scale(1)`)
            }


        },
        populateTooltip(evt, path) {
            this.tooltip.y = `${evt.pageY}px`
            this.tooltip.x = `${evt.pageX}px`
            this.tooltip.values.area_name = path.properties.area_name
            this.tooltip.values.value = path.value
            this.showTooltip = true
        },
        removeTooltip() {
            this.showTooltip = false
        }
    },
    watch: {
        zoomedValue: function (val) {
            this.zoomAndEmitClick(val)
        }
    }
}
</script>

<style scoped>
path {
    stroke: #a9a9a9;
    stroke-width: 0.5;
    stroke-linejoin: round;
    opacity: 1;
}

.tooltipContainer {
    position: absolute;
    font-size: 0.8rem;
    padding: 10px;
    border: solid 1px black;
    box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.4);
    background-color: #ffffff;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s;
}

.activeTooltip {
    opacity: 0.9;
    transition: opacity 0.3s;
}
</style>