<template>
    <div class="dashboard">

        <PanelContainer class="panelView"></PanelContainer>

        <MapContainer class="map"></MapContainer>

        <TopCausesContainer class="topCauses"></TopCausesContainer>

        <DemographicsContainer class="demographics"></DemographicsContainer>

    </div>
</template>

<script>
import TopCausesContainer from "@/components/TopCausesContainer";
import DemographicsContainer from "@/components/DemographicsContainer";
import MapContainer from "@/components/MapContainer";
import PanelContainer from "@/components/PanelContainer";

export default {
    name: "Dashboard",
    components: {
        PanelContainer,
        MapContainer,
        DemographicsContainer,
        TopCausesContainer,
    },
    data() {
        return {}
    },
    created() {
        this.$store.dispatch('loadData')
    }

}
</script>

<style scoped>
.dashboard {
    height: 100%;
    background-color: #dbdbdb;
    font-size: 0.88rem;
    box-sizing: border-box;
    padding: 10px;
    display: grid;
    grid-template-rows: repeat(5, minmax(0, 1fr));
    grid-template-columns: repeat(5, minmax(0, 1fr));
    grid-gap: 10px;
}

.dashboard > section {
    text-align: center;
    background-color: white;
    border-radius: 5px;
    box-shadow: none;
    transition: box-shadow 0.2s ease-in-out;
    height: 100%;
    padding: 5px;
}

section:hover {
    box-shadow: 0 10px 6px -6px #8f8f8f;
}

.panelView {
    grid-column: 1 / 4;
    grid-row: 1 / 3;
}

.map {
    grid-column: 1 / 4;
    grid-row: 3 / 6;
}

.topCauses {
    grid-column: 4 / 6;
    grid-row: 1 / 4;
}

.demographics {
    grid-column: 4 / 6;
    grid-row: 4 / 6;
}

</style>