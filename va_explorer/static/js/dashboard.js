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
            locations: [],
            map: null,
            geojson: {},
            layer: null,

            demographicsHeight: 0,
            demographicsWidth: 0,
            codHeight: 0,
            codWidth: 0,

            topCausesLimit: 50,
            startDate: "",
            causeSelected: "",
            borderType: "District"
        }
    },
    computed: {
        listOfCauses() {
            return [...new Set(this.rawdata.map(item => item.cause))].sort()
        },
        filteredData() {
            return this.rawdata
                .filter(item => item.active)
                .map(item => ({
                    ...item,
                    province: item.province.split(' ')[0],
                    district: item.district.split(' ')[0]
                }))
        },
        highlightsSummaries() {
            return {
                "Coded VAs": this.filteredData.length,
                "Uncoded VAs": this.invalid.length,
                "Active Facilities": [...new Set(this.filteredData.map(item => item.location))].length,
                "Placeholder": 0,
            }
        },
        geographicSums() {
            let geo_groups = d3.rollups(this.filteredData, v => v.length, d => d[this.borderType.toLowerCase()])
            let map = Object.fromEntries(geo_groups)
            return map
        },
        gender() {
            let groupby_gender_age = d3.rollups(this.filteredData,
                v => v.length,
                d => d.age_group_named, d => d.Id10019)
            return groupby_gender_age.map(gender => ({age_group_named: gender[0], ...Object.fromEntries(gender[1])}))
        },
        placeOfDeath() {
            let grouped = d3.rollups(this.filteredData, v => v.length, d => d.Id10058)
            return grouped
                .map(item => ({place: item[0].slice(0, 15), value: item[1]}))
                .sort((a, b) => b.value - a.value)
        },
        topCauses() {
            let grouped = d3.rollup(this.filteredData, v => v.length, d => d.cause)
            let map = Object.fromEntries(grouped)
            const causes = Object.keys(map)
                .map(item => ({cause: `${item.slice(0, 15)}...`, value: map[item]}))
                .sort((a, b) => b.value - a.value)
            return causes.slice(0, this.topCausesLimit)
        },
        ageGroup() {
            let grouped = d3.rollup(this.filteredData, v => v.length, d => d.age_group)
            let map = Object.fromEntries(grouped)
            return Object.keys(map).map(item => ({name: item, value: map[item]}))
        },
        allCausesTrend() {
            let dates = this.filteredData.map(item => ({date: this.getMonth(new Date(item.date)).toLocaleDateString()}))
            let grouped = d3.rollup(dates, v => v.length, d => d.date)
            let map = Object.fromEntries(grouped)
            return Object.keys(map)
                .map(item => ({date: item, value: map[item]}))
                .sort((a, b) => new Date(a.date) - new Date(b.date))
        },
    },
    async created() {
        /*
        Request data from API endpoint
         */
        this.csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const res = await fetch('http://localhost:8000/va_analytics/api/dashboard', {
            method: 'GET',
            headers: {'X-CSRFToken': this.csrftoken, 'Content-Type': 'application/json'},
            mode: 'same-origin'
        })

        const jsonRes = await res.json()
        this.rawdata = jsonRes.data.valid.map(item => ({...item, active: true}))
        this.invalid = jsonRes.data.invalid
        this.locations = jsonRes.locations

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
                    return {opacity: 0.9, weight: 1, dashArray: '2', color: 'red'}
                }
            }).addTo(this.map)
        },
        getMonth(date) {
            const month = date.getUTCMonth()
            const year = date.getUTCFullYear()
            return new Date(year, month, 0)
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
            this.startDate = null
            this.causeSelected = ""
            this.rawdata = this.rawdata.map(item => ({...item, active: true}))
        },
        filterByCauseOfDeath(COD) {
            if (COD) {
                this.rawdata = this.rawdata.map(item => ({...item, active: item.cause === COD}))
            } else {
                this.rawdata = this.rawdata.map(item => ({...item, active: true}))
            }
        },
        filterByDate(startDate) {
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
