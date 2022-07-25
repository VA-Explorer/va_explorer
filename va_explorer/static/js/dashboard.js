Vue.use('stacked-bar-chart', 'line-chart')

const dashboard = new Vue({
    el: '#dashboardApp',
    delimiters: ["<%", "%>"],
    data() {
        return {
            csrftoken: "",

            rawdata: [],
            invalid: "",
            location_types: [],
            locations: [],

            demographicsHeight: 0,
            demographicsWidth: 0,
            codHeight: 0,
            codWidth: 0,

            topCausesLimit: 50,
            startDate: "",
            causeSelected: "",
        }
    },
    computed: {
        listOfCauses() {
            return [...new Set(this.rawdata.map(item => item.cause))].sort()
        },
        listOfDistrictAndProvinces() {
            const provinces = [...new Set(this.rawdata.map(item => item.province))]
            const districts = [...new Set(this.rawdata.map(item => item.district))]
            return [...provinces, ...districts].sort()
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
            let geo_groups = d3.rollups(this.filteredData, v => v.length, d => d[state.borders])
            let map = Object.fromEntries(geo_groups)
            return Object.keys(map).map(item => ({geography: item, value: map[item]}))
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
        }
    },
    async created() {
        this.csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const res = await fetch('http://localhost:8000/va_analytics/api/dashboard', {
            method: 'GET',
            headers: {'X-CSRFToken': this.csrftoken, 'Content-Type': 'application/json'},
            mode: 'same-origin'
        })

        const jsonRes = await res.json()
        this.rawdata = jsonRes.data.valid.map(item => ({...item, active: true}))
        this.invalid = jsonRes.data.invalid
        this.location_types = jsonRes.location_types
        this.locations = jsonRes.locations
        console.log(jsonRes)
    },
    mounted() {
        this.resizeCharts()
        window.addEventListener('resize', this.resizeCharts)
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.resizeCharts)
    },
    methods: {
        getMonth(date) {
            const month = date.getUTCMonth()
            const year = date.getUTCFullYear()
            return new Date(year, month, 0)
        },
        resizeCharts() {
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
    }
})
