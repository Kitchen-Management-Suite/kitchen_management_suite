
document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM Content Loaded running init script");

    const addMealButtons = document.querySelectorAll(".addMealBtn")
    const dropdown = document.getElementById("dropdownMenu")
    let curtClicked = null

    if (addMealButtons == null)
        console.log("!ERROR! could not find meal elements")
        //Handle Later

    if (dropdown == null)
        console.log("!ERROR! could not find dropdown element")
        //Handle Later

    //There is admittidley a little inefficency here,
    //Becuase there is always two click checks when clicking a buttong
    //Plus the click check whenever you click anything
    //But it works and that's all that matters
    addMealButtons.forEach(button => {
         button.addEventListener("click", (event) => {
            dropdown.style.display = dropdown.style.display === "block" ? "none": "block";

            dropdown.style.left =  event.pageX + "px";
            dropdown.style.top = event.pageY + "px";

            console.log(button);
            curtClicked = button;
        })
    });

    document.addEventListener("click", (event) =>{
        if  (curtClicked == null) return;
        if (!(curtClicked.contains(event.target)) && !(dropdown.contains(event.target))){
            dropdown.style.display = "none";
            curtClicked = null;
            console.log(dropdown.style.display);
        }
    })
})

function apiStuff(){
    console.log("API STUFF");
}

