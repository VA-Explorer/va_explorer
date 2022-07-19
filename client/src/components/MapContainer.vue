<template>
    <section class="mapPanel">
        <h2>Map</h2>
        <div class="controls">
            <label for="mapview">Map View:</label>
            <div class="select is-small">
                <select id="mapview" v-model="mapDisplay" @change="changeBorders($event.target.value)">
                    <option v-for="option in mapDisplayOptions" :key="option">{{ option }}</option>
                </select>
            </div>
            <label for="searchlocations" class="sr-only">Search Locations (or click on map)</label>
            <v-select id="searchlocations" :options="listOfDistrictAndProvinces" v-model="searchInput"
                      @input="searchAndFilterMap($event)">
            </v-select>
        </div>
        <div ref="mapContainer" class="mapContainer">
            <Choropleth :geojson="borders" :plot-data="geoData" :zoomed-value="searchInputGeo"
                        :width="width" :height="height" :margin="margin"
                        @click="zoomAndFilterMap($event)">
                <template v-slot:tooltip="{ row }">
                    <p>{{ row.area_name }}</p>
                    <p>{{ row.value ? `All Causes: ${row.value}` : 'No Data' }}</p>
                </template>
            </Choropleth>
        </div>
        <div class="scale">
            <ColorScale :width="width" :height="height" :margin="margin_colorScale"
                        :geo-data="geoData" :color-scale="colorScale">
            </ColorScale>
        </div>
    </section>
</template>

<script>
import geojson from '../../public/zambia_geojson.json'
import Choropleth from "@/components/Choropleth";
import ColorScale from "@/components/ColorScale";
import {mapGetters, mapMutations} from "vuex";
import vSelect from "vue-select";
import 'vue-select/dist/vue-select.css'
import {scaleSequential} from "d3-scale";
import {interpolateRdYlBu} from "d3-scale-chromatic";
import {extent} from "d3-array";

export default {
    name: "MapContainer",
    components: {
        Choropleth,
        vSelect,
        ColorScale
    },
    data() {
        return {
            geojson: geojson,
            width: null,
            height: null,
            margin: {top: 10, bottom: 10, left: 10, right: 10},
            margin_colorScale: {top: 10, bottom: 10, left: 40, right: 10},
            mapDisplay: "District",
            mapDisplayOptions: ["Province", "District"],
            zoom: false,
            searchInput: null,
            searchInputGeo: null,
        }
    },
    computed: {
        ...mapGetters(['geographicSums', 'listOfDistrictAndProvinces']),
        geoData() {
            return this.geographicSums.map(item => ({...item, color: this.colorScale(item.value)}))
        },
        colorScale() {
            return scaleSequential(interpolateRdYlBu)
                .domain(extent(this.geographicSums, d => d.value).reverse())
                .nice()
        },
        borders() {
            const border_types = ["Country", "Province"]
            if (this.mapDisplay === "District") border_types.push("District")

            let features = this.geojson.features
                .filter(item => border_types.includes(item.properties.area_level_label))
                .map(item => ({
                    ...item,
                    ...this.findValueAndColor(item.properties.area_name, this.geoData)
                }))
            return {...geojson, features}
        },

    },
    methods: {
        ...mapMutations(['changeBorders', 'filterByDistrict']),
        findValueAndColor(area_name) {
            let item = this.geoData.find(item => item.geography === area_name)
            return item ? {color: item.color, value: item.value} : {color: '#f3f3f3', value: ''}
        },
        getProvinceGivenID(province_id) {
            return this.geojson.features.find(e => e.properties.area_id === province_id).properties.area_name
        },
        searchAndFilterMap(evt) {
            if (!evt) {
                this.zoom = false
                this.searchInputGeo = null
                this.filterByDistrict({district: null, province: null})
                return
            }
            const search = evt.split(" ")
            if (search[1] === "District") {
                this.searchInputGeo = this.geojson.features.find(e =>
                    e.properties.area_name === search[0] && e.properties.area_level_label === "District")
            } else if (search[1] === "Province") {
                this.searchInputGeo = this.geojson.features.find(e =>
                    e.properties.area_name === search[0] && e.properties.area_level_label === "Province")
            }
        },
        zoomAndFilterMap(evt) {
            this.zoom = !this.zoom
            if (!this.zoom) {
                this.filterByDistrict({district: null, province: null})
            } else {
                if (evt.properties.area_level_label === "District") {
                    let province_id = evt.properties.parent_area_id
                    let province = this.getProvinceGivenID(province_id)
                    let data = {district: evt.properties.area_name, province: province}
                    this.filterByDistrict(data)
                } else if (evt.properties.area_level_label === "Province") {
                    this.mapDisplay = "District"
                    let data = {district: null, province: evt.properties.area_name}
                    this.changeBorders("District")
                    this.filterByDistrict(data)
                }
            }
        },
        resizeWidthAndHeight() {
            this.width = this.$refs.mapContainer.clientWidth - 1
            this.height = this.$refs.mapContainer.clientHeight - 1
        }
    },
    mounted() {
        this.resizeWidthAndHeight()
        window.addEventListener('resize', this.resizeWidthAndHeight)
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.resizeWidthAndHeight)
    },
}
</script>

<style scoped>
.mapPanel {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: 20px repeat(5, 1fr);
}

h2 {
    grid-column: 1 / 5;
    grid-row: 1 / 2;
    font-weight: bold;
    font-size: 0.95rem;
}

.controls {
    grid-column: 1 / 5;
    grid-row: 2 / 3;
    display: flex;
    align-items: center;
}

.controls > label {
    margin: 0 0.75rem;
    font-size: 0.85rem;
}

#searchlocations {
    width: 40%;
    margin-left: 1rem;
}

.mapContainer {
    grid-row: 3 / 7;
    grid-column: 1 / 4;
}

.scale {
    grid-row: 3 / 7;
    grid-column: 4 / 5;
}

</style>
