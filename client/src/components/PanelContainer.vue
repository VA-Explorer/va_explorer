<template>
    <section>
        <h2>Summaries and Control Panel</h2>
        <div class="controls">
            <label for="causeSelected">Cause of Death</label>
            <div class="select is-small">
                <select id="causeSelected" v-model="causeSelected"
                        @change="$store.commit('filterByCauseOfDeath', $event.target.value)">
                    <option></option>
                    <option v-for="cause in listOfCauses" :key="cause">{{ cause }}</option>
                </select>
            </div>
            <label for="startDate">Start Date:</label>
            <input id="startDate" class="input is-small" type="date" required v-model="startDate"
                   @change="$store.commit('filterByDate', $event.target.value)">
            <button type="button" class="button is-small" @click="clearAll()">Reset</button>
        </div>
        <div class="highlightsContainer">
            <DashboardMarker v-for="(value, key) in highlightsSummaries" :key="key"
                             :title="key" :amount="value">
            </DashboardMarker>
        </div>
    </section>
</template>

<script>
import {mapGetters} from 'vuex'
import DashboardMarker from "@/components/DashboardMarker";

export default {
    name: "PanelContainer",
    components: {
        DashboardMarker
    },
    data() {
        return {
            causeSelected: "",
            startDate: null,
        }
    },
    computed: {
        ...mapGetters(['listOfCauses', 'highlightsSummaries']),
    },
    methods: {
        clearAll() {
            this.startDate = null
            this.causeSelected = ""
            this.$store.commit('resetAllDataToActive')
        }
    }
}
</script>

<style scoped>
h2 {
    height: 20px;
    font-weight: bold;
    font-size: 0.95rem;
}

.controls {
    height: 25%;
    display: flex;
    align-items: center;
}

.controls label {
    margin: 0 8px;
    font-size: 0.82rem;
    width: auto;
}

.button {
    margin-left: 10px;
}

.highlightsContainer {
    height: calc(100% - 25% - 30px);
    display: flex;
    align-items: center;
    padding: 20px 10px;
}

</style>
