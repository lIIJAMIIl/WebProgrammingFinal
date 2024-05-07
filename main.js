const app = Vue.createApp({
    delimiters: ['${' , '}'],
    data() {
        return {
            user: '',
            sessionID: '',
            numVisits: 0,
            quotes: [],
        }
    },
    mounted() {
        console.log("Mounted is called")
        axios.get('/')
        .then( response => {
            console.log("API response: ", response);
            this.quotes = response.data;
            this.user = response.user;
            this.numVisits = response.numVisits;
            this.sessionID = response.sessionID;
        })
        .catch(error => {
            console.error('Error fetching quotes: ', error);
        });
    }
})