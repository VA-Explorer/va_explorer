<template>
    <section>
        <h2>Cause Of Death Analysis</h2>
        <div class="controls">
            <label for="limit">Limit</label>
            <div class="select is-small">
                <select id="limit" v-model="topCausesLimit">
                    <option v-for="limit in topCausesLimitValues" :key="limit">{{ limit }}</option>
                </select>
            </div>
        </div>
        <div ref="topCauses" class="chartsContainer">
            <div class="topCausesContainer">
                <StackedBarChart v-if="topCauses.length > 0"
                                 :plot-data="topCausesFiltered" x-key="cause"
                                 direction="horizontal" bar-axis-location="top"
                                 :width="width" :height="70 + 18 * topCausesFiltered.length"
                                 :margin="{top: 20, bottom: 20, left: 90, right: 30}"
                                 :colors="['#23689b']">
                </StackedBarChart>
            </div>

            <div class="topCauseLineChartContainer">
                <LineChart v-if="allCausesTrend.length > 0"
                           :plot-data="allCausesTrend" x-key="date"
                           :width="width" :height="height / 2"
                           :margin="{top:20, bottom: 20, left: 40, right: 20}"
                           :colors="['#23689b']">
                </LineChart>
            </div>
        </div>
    </section>
</template>

<script>
import {mapGetters} from 'vuex';


export default {
    name: "TopCausesContainer",
    data() {
        return {
            topCausesLimit: 10,
            topCausesLimitValues: [10, 20, 30, 40, 50, 100],
            width: null,
            height: null,
        }
    },
    computed: {
        ...mapGetters(['topCauses', 'allCausesTrend']),
        topCausesFiltered() {
            return this.topCauses.slice(0, this.topCausesLimit)
        }
    },
    methods: {
        resizeWidthAndHeight() {
            this.width = this.$refs.topCauses.clientWidth - 1
            this.height = this.$refs.topCauses.clientHeight - 1
        },
    },
    mounted() {
        this.resizeWidthAndHeight()
        window.addEventListener('resize', this.resizeWidthAndHeight)
    }
}
</script>

<style scoped>
section {
    display: flex;
    flex-direction: column;
    --header-height: 25px;
    --controls-height: 12%;
    --charts-container-height: calc(100% - var(--controls-height) - var(--header-height));
}

h2 {
    height: var(--header-height);
    font-weight: bold;
    font-size: 0.95rem;
}

.controls {
    height: var(--controls-height);
    display: flex;
    justify-content: flex-start;
    align-items: center;
}

.controls > .select {
    width: 20%;
}

.controls select {
    height: 100%;
    width: 100%;
}

.controls > label {
    margin: 0 10px;
}

.chartsContainer {
    height: var(--charts-container-height);
    display: flex;
    flex-direction: column;
}

.topCausesContainer {
    height: 50%;
    overflow-y: scroll;
    overflow-x: hidden;
}

.topCauseLineChartContainer {
    height: 50%;
}
</style>
