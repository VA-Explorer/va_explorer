// todo: percent/count toggle

Vue.use('stacked-bar-chart', 'line-chart', 'loader-spinning')

const dashboard = new Vue({
    el: '#dashboardApp',
    delimiters: ["<%", "%>"],
    data() {
        return {
            csrftoken: "",

            // map related values
            map: null,
            geojson: {},
            layer: null,

            // default values for all the charts
            COD_grouping: [],
            COD_trend: [],
            place_of_death: [],
            demographics: [],
            geographic_province_sums: null,
            geographic_district_sums: null,
            uncoded_vas: 0,
            update_stats: {
                last_update: 0,
                last_interview: 0,
            },

            // chart sizes
            demographicsHeight: 0,
            demographicsWidth: 0,
            codHeight: 0,
            codWidth: 0,

            // dropdowns options and selected values
            listOfCausesDropdownOptions: [],
            locationTypesDropdownOptions: ["Province", "District"],
            deathDateDropdownOptions: ["Any Time", "Within 1 Month", "Within 3 months", "Within 1 year", "Custom"],
            deathDateSelected: "Any Time",
            startDate: "",
            endDate: "",
            causeSelected: "",
            regionSelected: "",
            ageSelected: "",
            sexSelected: "",
            borderType: "Province",


            colorScale: [
                "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf",
                "#fee090", "#fdae61", "#f46d43", "#d73027"
            ],

            demographicsLegendData: [
                {
                    name: "Female",
                    color: "#440154FF",
                },
                {
                    name: "Male",
                    color: "#404788FF",
                }
            ],

            loading: true,
            locations: [],
            suppressWarning: false,
            placeOfDeathValue: "count",
            causeOfDeathValue: "count",
        }
    },
    computed: {
        highlightsSummaries() {
            return {
                "Last Data Update": this.update_stats.last_update,
                "Last VA Interview": this.update_stats.last_interview,
                "Coded VAs": d3.sum(this.COD_grouping.map(item => item.count)),
                "Uncoded VAs": this.uncoded_vas,
            }
        },
        geographicSums() {
            if (this.borderType === 'Province') {
                return this.geographic_province_sums
            } else if (this.borderType === 'District') {
                return this.geographic_district_sums
            }
        },
        geoScale() {
            // A better way to do this would be to import d3 scale and use a quanitzed scale but import is large
            if (!this.geographicSums) return
            const geoMax = Math.max(...this.geographicSums.map(item => +item.count)) + 100
            const geoMin = 1
            const n = 10
            const step = (geoMax - geoMin) / (n - 1)
            return Array.from({length: n}, (_, i) => Math.round(geoMin + step * i))
        },
        placeOfDeathData() {
            if (!this.place_of_death) return [];
            if (this.placeOfDeathValue === "count") return this.place_of_death;
            const totalCount = d3.sum(this.place_of_death.map(item => item.count));
            return JSON.parse(JSON.stringify(this.place_of_death)).map(d => {
                d.percentage = Math.round(d.count * 1000 / totalCount) / 10;
                delete d.count;
                return d;
            })
        },
        causeOfDeathData() {
            if (!this.COD_grouping) return [];
            if (this.causeOfDeathValue === "count") return this.COD_grouping;
            const totalCount = d3.sum(this.COD_grouping.map(item => item.count));
            return JSON.parse(JSON.stringify(this.COD_grouping)).map(d => {
                d.percentage = Math.round(d.count * 1000 / totalCount) / 10;
                delete d.count;
                return d;
            })
        },
    },
    async created() {
        // Request data from API endpoint
        await this.getData()

        this.locations = this.geographic_province_sums.map(d => ({
            name: d.province_name,
            type: "Province",
        })).concat(this.geographic_district_sums.map(d => ({
            name: d.district_name,
            type: "District",
        })));
        this.locations.sort((a, b) => a.name > b.name ? 1 : b.name > a.name ? -1 : 0);

        // Request geojson data
        const url = `${window.location.protocol}//${window.location.hostname}:${window.location.port}/static/`
        const geojsonRes = await fetch(`${url}data/zambia_geojson.json`)
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
        async getData() {
            // fetch data for charts from API and assign all data variables for charts
            this.loading = true

            const {age, sex} = this.getAgeAndSex()
            const {startDate, endDate} = this.getStartAndEndDates()

            this.csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            const data_url = `${window.location.origin}/va_analytics/api/dashboard?`
            const dataReq = await fetch(data_url + new URLSearchParams({
                start_date: startDate,
                end_date: endDate,
                cause_of_death: this.causeSelected,
                region_of_interest: this.regionSelected,
                age, sex
            }), {
                method: 'GET',
                headers: {'X-CSRFToken': this.csrftoken, 'Content-Type': 'application/json'},
                mode: 'same-origin'
            })

            const jsonRes = await dataReq.json()
            this.COD_grouping = jsonRes.COD_grouping
            this.COD_trend = jsonRes.COD_trend
            this.place_of_death = jsonRes.place_of_death.map(d => {
                d.place = d.place.replace(/_/g, " ");
                return d;
            })
            this.demographics = jsonRes.demographics
            this.geographic_province_sums = jsonRes.geographic_province_sums
            this.geographic_district_sums = jsonRes.geographic_district_sums
            this.uncoded_vas = jsonRes.uncoded_vas
            this.update_stats = jsonRes.update_stats
            this.listOfCausesDropdownOptions = jsonRes.all_causes_list

            // if one or more age groups is absent from API data, add it with counts of zero
            // also add age ranges here (todo: modify API to do these things?)
            const ageGroups = ["neonate", "child", "adult"]
            for (const ageGroup of ageGroups) {
                let index = this.demographics.map(d => d.age_group).indexOf(ageGroup);
                if (index === -1) {
                    this.demographics.push({
                        female: 0,
                        male: 0,
                    });
                    index = this.demographics.length - 1;
                }
                if (!this.demographics[index].hasOwnProperty("female")) {
                    this.demographics[index].female = 0
                }
                if (!this.demographics[index].hasOwnProperty("male")) {
                    this.demographics[index].male = 0
                }
                this.demographics[index].age_group = ageGroup === "neonate" ? "Neonate (< 28 days)" :
                    ageGroup === "child" ? "Child (≤ 12 years)" : "Adult (> 12 years)";
                this.demographics[index].order = ageGroups.indexOf(ageGroup);
            }
            this.demographics.sort((a, b) => a.order > b.order ? 1 : b.order > a.order ? -1 : 0);
            this.demographics.forEach(d => {
                delete d.order;
            });

            // display warning message if small sample size (allow user to stop these dialogs)
            if (!this.suppressWarning &&
                d3.sum(this.COD_grouping.map(item => item.count)) < 50) {
                $("#small-sample-size-warning").modal().show();
            }

            this.loading = false
        },
        async initializeBaseMap() {
            // use to set base map with tile on initial load
            this.map = L.map('map', {
                maxBounds: [
                    [-6, 20],
                    [-20, 34],
                ]
            }).setView([-13, 27], 6)

            this.map.attributionControl.setPrefix('')
            this.map.keyboard.disable()

            const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 10,
                attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }).addTo(this.map)
        },
        addGeoJSONToMap() {
            // Remove any existing choropleth layer and add new layer with tooltip and coloring

            const vm = this
            if (this.layer) this.map.removeLayer(this.layer)

            const borders = ['Country', this.borderType]
            let geojson = JSON.parse(JSON.stringify(this.geojson))
            geojson.features = this.geojson.features.filter(feature => {
                return borders.includes(feature.properties.area_level_label)
            })

            this.layer = L.geoJson(geojson, {
                style: function (feature) {
                    if (feature.properties.area_level_label !== 'Country') {
                        const color = vm.getColor(feature)
                        return {stroke: true, weight: 2, color, opacity: 1, fillColor: color, fillOpacity: 0.7}
                    } else {
                        return {weight: 2.5, opacity: 1, color: 'grey', stroke: true}
                    }
                },
                onEachFeature: function (feature, layer) {
                    const html_tooltip = vm.generateTooltip(feature)
                    layer.bindTooltip(html_tooltip)
                    layer.on("click", async (e) => {
                        const geoproperty = e.target.feature.properties
                        vm.regionSelected = `${geoproperty.area_name} ${geoproperty.area_level_label}`
                        await vm.getData()
                    })
                }
            }).addTo(this.map)
        },
        getMonth(date) {
            // Extract year and month for line chart
            const month = date.getUTCMonth()
            const year = date.getUTCFullYear()
            return new Date(year, month, 0)
        },
        getColor(feature) {
            // Returns appropriate color for regions on map
            const {area_name, area_level_label} = feature.properties
            const area = `${area_name} ${area_level_label}`
            const geo_sums = this.borderType === 'Province' ? this.geographic_province_sums : this.geographic_district_sums
            const geo_accessor = this.borderType === 'Province' ? 'province_name' : 'district_name'

            const results = geo_sums.find(item => item[geo_accessor] === area)
            if (results) {
                const count = results.count
                for (let i = 0; i < this.geoScale.length; i++) {
                    if (count >= this.geoScale[i] && count < this.geoScale[i + 1]) {
                        return this.colorScale[i]
                    }
                }
            } else {
                return '#c0c0c0'
            }
        },
        getAgeAndSex(){
            // return lower cased version of age and sex for request
            const age = this.ageSelected.toLowerCase()
            const sex = this.sexSelected.toLowerCase()

            return {age, sex}
        },
        getStartAndEndDates() {
            // Generate start and end dates based on death date drop down options

            let date
            switch (this.deathDateSelected) {
                case "Any Time":
                    return {startDate: "", endDate: ""}
                case "Within 1 Month":
                    date = new Date()
                    date.setMonth(date.getMonth() - 1)
                    return {startDate: date.toISOString().slice(0, 10), endDate: ""}
                case "Within 3 months":
                    date = new Date()
                    date.setMonth(date.getMonth() - 3)
                    return {startDate: date.toISOString().slice(0, 10), endDate: ""}
                case "Within 1 year":
                    date = new Date()
                    date.setFullYear(date.getFullYear() - 1)
                    return {startDate: date.toISOString().slice(0, 10), endDate: ""}
                case "Custom":
                    return {startDate: this.startDate, endDate: this.endDate}
            }
        },
        generateTooltip(feature) {
            // create tooltip for leaflet map

            const vm = this

            const area_level_label = feature.properties.area_level_label
            const area_name = feature.properties.area_name
            let count = 0
            if (area_level_label === 'District') {
                let district = vm.geographic_district_sums
                    .filter(item => item.district_name)
                    .find(item => item.district_name.includes(area_name))
                if (district) {
                    count = district.count
                }
            } else if (area_level_label === 'Province') {
                let province = vm.geographic_province_sums
                    .filter(item => item.province_name)
                    .find(item => item.province_name.includes(area_name))
                if (province) {
                    count = province.count
                }
            }
            const html_tooltip = `
                    <div class="mapTooltip">
                        <h4>${area_name} ${area_level_label}</h4>
                        <p>${count}</p>
                    </div>
                    `
            return html_tooltip
        },
        resizeCharts() {
            // Apply method on mounted and with window event listener to automatically resize charts

            this.demographicsWidth = this.$refs.demographics.clientWidth - 1
            this.demographicsHeight = this.$refs.demographics.clientHeight - 1

            this.codWidth = this.$refs.cod.clientWidth - 1
        },
        async updateDataAndMap() {
            await this.getData()
            this.addGeoJSONToMap()
        },
        async resetAllDataToActive() {
            // reset all dashboard filters and retrieve the initial data
            this.startDate = ""
            this.endDate = ""
            this.causeSelected = ""
            this.deathDateSelected = "Any Time"
            this.regionSelected = ""
            this.ageSelected = ""
            this.sexSelected = ""
            await this.updateDataAndMap()
        },
    },
    watch: {
        // assign watchers to update map choropleth since it does not happen automatically
        geojson() {
            this.addGeoJSONToMap()
        },
        borderType() {
            this.addGeoJSONToMap()
        },
    }
})
