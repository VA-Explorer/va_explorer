<template>
    <div id="app">
        <Dashboard></Dashboard>
    </div>
</template>

<script>
import Dashboard from "@/components/Dashboard";

export default {
    name: 'App',
    components: {
        Dashboard
    }
}
</script>

<style>
body {
    margin: 0;
    padding: 0;
    height: 100vh;
    overflow-y: hidden;
}

#app {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    height: 100%;
}

#app .tick text {
    fill: #1c1c1c;
    text-rendering: optimizeLegibility;
}
</style>
