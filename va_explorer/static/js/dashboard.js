Vue.use('stacked-bar-chart', 'line-chart', 'loader-spinning')

const dashboard = new Vue({
    el: '#dashboardApp',
    delimiters: ["<%", "%>"],
    data() {
        return {
            csrftoken: "",

            rawdata: [],
            invalid: "",
            location_types: ["Province", "District"],
            map: null,
            geojson: {},
            layer: null,

            COD_grouping: null,
            COD_trend: null,
            place_of_death: null,
            demographics: null,
            geographic_province_sums: null,
            geographic_district_sums: null,
            cause_stats: null,

            demographicsHeight: 0,
            demographicsWidth: 0,
            codHeight: 0,
            codWidth: 0,

            topCausesLimit: 50,
            startDate: "",
            causeSelected: "",
            borderType: "Province"
        }
    },
    computed: {
        listOfCauses() {
            if (this.COD_grouping) {
                return this.COD_grouping.map(item => item.cause).sort()
            } else {
                return []
            }
        },
        highlightsSummaries() {
            if (this.cause_stats) {
                return {
                    "Coded VAs": this.cause_stats.find(item => item.valid_cause).count,
                    "Uncoded VAs": this.cause_stats.find(item => !item.valid_cause).count,
                    "Placeholder 1": 0,
                    "Placeholder 2": 0,
                }
            } else {
                return {}
            }
        },
        geographicSums() {
            if (this.borderType === 'Province') {
                return this.geographic_province_sums
            } else if (this.borderType === 'District') {
                return this.geographic_district_sums
            }
        },
        locations() {
            if (!this.geographic_province_sums || !this.geographic_district_sums) return []
            const provinces = this.geographic_province_sums.map(item => item.province_name)
            const districts = this.geographic_district_sums.map(item => item.district_name)
            return [...provinces, ...districts]
        }
    },
    async created() {
        /*
        Request data from API endpoint
         */
        this.csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const dataReq = await fetch('http://localhost:8000/va_analytics/api/dashboard', {
            method: 'GET',
            headers: {'X-CSRFToken': this.csrftoken, 'Content-Type': 'application/json'},
            mode: 'same-origin'
        })

        const jsonRes = await dataReq.json()
        this.COD_grouping = jsonRes.COD_grouping
        this.COD_trend = jsonRes.COD_trend
        this.place_of_death = jsonRes.place_of_death
        this.demographics = jsonRes.demographics
        this.geographic_province_sums = jsonRes.geographic_province_sums
        this.geographic_district_sums = jsonRes.geographic_district_sums
        this.cause_stats = jsonRes.cause_stats

        // Request geojson data
        const url = `${window.location.protocol}//${window.location.hostname}:${window.location.port}/static/`
        const geojsonRes = await fetch(`${url}/data/zambia_geojson.json`)
        this.geojson = await geojsonRes.json()
    },
    async mounted() {
        this.resizeCharts()
        window.addEventListener('resize', this.resizeCharts)

        await this.initializeBaseMap()
    },
    beforeDestroy() {
        // necessary to remove resize listener to avoid memory leak after switching to different view
        window.removeEventListener('resize', this.resizeCharts)
    },
    methods: {
        async initializeBaseMap() {
            this.map = L.map('map').setView([-13, 27], 6)

            this.map.attributionControl.setPrefix('')

            const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 10,
                attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }).addTo(this.map)
        },
        addGeoJSONToMap() {
            const vm = this
            if (this.layer) {
                this.map.removeLayer(this.layer)
            }

            const borders = ['Country', this.borderType]
            let geojson = JSON.parse(JSON.stringify(this.geojson))
            geojson.features = this.geojson.features.filter(feature => {
                return borders.includes(feature.properties.area_level_label)
            })
            this.layer = L.geoJson(geojson, {
                style: function (feature) {
                    if (feature.properties.area_level_label !== 'Country') {
                        const color = vm.getColor(feature)
                        return {stroke: true, weight: 1, color, opacity: 1, fillColor: color, fillOpacity: 0.3}
                    } else {
                        return {weight: 2, opacity: 1, color: 'grey', stroke: true}
                    }
                }
            }).addTo(this.map)
        },
        getMonth(date) {
            const month = date.getUTCMonth()
            const year = date.getUTCFullYear()
            return new Date(year, month, 0)
        },
        getColor(feature) {
            const {area_name, area_level_label} = feature.properties
            const area = `${area_name} ${area_level_label}`
            const geo_sums = this.borderType === 'Province' ? this.geographic_province_sums : this.geographic_district_sums
            const geo_accessor = this.borderType === 'Province' ? 'province_name' : 'district_name'

            const results = geo_sums.find(item => item[geo_accessor] === area)
            if (results) {
                return results.count > 1000 ? 'red' : 'blue'
            } else {
                return '#797979'
            }
        },
        resizeCharts() {
            /*
            Apply method on mounted and with event listener to automatically resize charts
             */
            this.demographicsWidth = this.$refs.demographics.clientWidth - 1
            this.demographicsHeight = this.$refs.demographics.clientHeight - 1

            this.codWidth = this.$refs.cod.clientWidth - 1
            this.codHeight = this.$refs.cod.clientHeight - 1
        },
        resetAllDataToActive() {
            // TODO use original API request
            this.startDate = null
            this.causeSelected = ""
        },
        filterByCauseOfDeath(COD) {
            // TODO make COD a query param in API request
            if (COD) {
                this.rawdata = this.rawdata.map(item => ({...item, active: item.cause === COD}))
            } else {
                this.rawdata = this.rawdata.map(item => ({...item, active: true}))
            }
        },
        filterByDate(startDate) {
            // TODO make date a query param in API request
            this.rawdata = this.rawdata.map(item => ({...item, active: new Date(startDate) < new Date(item.date)}))
        },
    },
    watch: {
        geojson() {
            this.addGeoJSONToMap()
        },
        borderType() {
            this.addGeoJSONToMap()
        },
    }
})
