<template>
    <div>
        <h3>{{ title }}</h3>
        <p>{{ amount }}</p>
    </div>
</template>

<script>
export default {
    name: "DashboardMarker",
    props: {
        title: String,
        amount: Number
    }
}
</script>

<style scoped>
div {
    width: 20%;
    margin: 10px;
    border: solid 1px #d0d0d0;
    border-radius: 4px;
}

h3 {
    padding: 5px;
    border-bottom: solid 1px #cdcdcd;
    background-color: #e5e5e5;
    font-weight: normal;
    font-size: 0.9rem;
}

p {
    background-color: #f3f3f3;
    padding: 15px;
    font-weight: bold;
    font-size: 1.2rem;
}
</style>
