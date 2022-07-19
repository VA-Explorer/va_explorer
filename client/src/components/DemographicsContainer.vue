<template>
    <section>
        <h2>All Cause Demographics</h2>
        <div ref="demographics" class="chartContainer">
            <div class="genderAgeStack">
                <BaseLegend :legend-data="genderLegend"></BaseLegend>
                <StackedBarChart v-if="gender.length > 0"
                                 :plot-data="gender" x-key="age_group"
                                 :width="width * (2/5)" :height="height"
                                 :margin="{top: 5, bottom: 30, left: 40, right: 20}"
                                 :colors="['#10437a', '#c1a1d3']">
                </StackedBarChart>
            </div>
            <div class="placeOfDeathContainer">
                <StackedBarChart v-if="placeOfDeath.length > 0"
                                 :plot-data="placeOfDeath" x-key="place" direction="horizontal"
                                 :width="width * (3/5)" :height="height + 20"
                                 :margin="{top: 30, bottom: 20, left: 90, right: 10}"
                                 :colors="['#23689b']">
                </StackedBarChart>

            </div>
        </div>
    </section>
</template>

<script>
import {mapGetters} from 'vuex';

export default {
    name: "DemographicsContainer",
    data() {
        return {
            width: null,
            height: null,
            genderLegend: [{name: "male", color: "#10437a"}, {name: "female", color: "#c1a1d3"}]
        }
    },
    computed: {
        ...mapGetters(['gender', 'placeOfDeath'])
    },
    mounted() {
        this.resizeWidthAndHeight()
        window.addEventListener('resize', this.resizeWidthAndHeight)
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.resizeWidthAndHeight)
    },
    methods: {
        resizeWidthAndHeight() {
            this.width = this.$refs.demographics.clientWidth - 1
            this.height = this.$refs.demographics.clientHeight - 25
        }
    }
}
</script>

<style scoped>
section {
    display: flex;
    flex-direction: column;
}

section h2 {
    height: 20px;
    font-weight: bold;
    font-size: 0.95rem;
}

.chartContainer {
    height: calc(100% - 20px);
    display: flex;
}

.genderAgeStack {
    display: flex;
    flex-direction: column;
    width: 40%;
}

.placeOfDeathContainer {
    width: 60%;
}
</style>
