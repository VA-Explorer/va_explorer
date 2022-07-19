<template>
    <svg :height="height" :width="width / 4" v-if="geoData.length > 0">
        <g v-scaleaxis="{yscale: yScale}"
           class="sequentialScale"
           :transform="`translate(${this.margin.left + 10} ${this.margin.top})`">
        </g>
        <rect v-for="tick in yScale.ticks(8).reverse()" :key="`tick-${tick}`"
              :width="10" :height="(height) / yScale.ticks(8).length"
              :x="margin.left" :y="yScale(tick) - margin.bottom"
              :fill="colorScale(tick)">
        </rect>
    </svg>
</template>

<script>
import {scaleLinear} from "d3-scale";
import {extent} from "d3-array";
import {select} from "d3-selection";
import {axisRight} from "d3-axis";
import {mapGetters} from "vuex";

export default {
    name: "ColorScale",
    props: {
        width: Number,
        height: Number,
        margin: Object,
        geoData: Array,
        colorScale: Function,
    },
    computed: {
        ...mapGetters(["geographicSums"]),
        yScale() {
            return scaleLinear()
                .domain(extent(this.geographicSums, d => d.value).reverse())
                .range([this.margin.bottom, this.height - this.margin.top - this.margin.bottom])
                .nice()
        },
    },
    directives: {
        scaleaxis(el, binding) {
            let yscale = binding.value.yscale
            select(el).call(axisRight(yscale).ticks(8)).select("path").style("stroke", "none")
        }
    }
}
</script>

<style scoped>

</style>