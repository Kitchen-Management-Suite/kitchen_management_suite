document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM Content Loaded running init script");


    const addMealButtons = document.querySelectorAll(".typeMealSelc")
    const defaultMealType = document.getElementById("defMealType")
    const addFoodToLog = document.getElementById("addFoodToLog")
    const removeFoodItem = document.querySelectorAll(".removeItem")

    let curtClicked = defaultMealType
    //Default is hardcoded in calorieTracking html
    
    if (addMealButtons == null || defMealType == null || addFoodToLog == null)
        console.log("!ERROR! could not find meal elements")
        //Handle Later

    // console.log(defaultMealType)
    defaultMealType.style.background = "#bbdefb";

    //There is admittidley a little inefficency here,
    //Becuase there is always two click checks when clicking a buttong
    //Plus the click check whenever you click anything
    //But it works and that's all that matters

    addMealButtons.forEach(button => {
         button.addEventListener("click", (event) => {
            // console.log("TEST");
            // console.log(event.target);
            if (curtClicked != null){
                curtClicked.style.background = "unset";
            }
            button.style.background = "#bbdefb";
            mealType = button.innerHTML;
            curtClicked = button;
            console.log(document.getElementsByName("MealType"))
            document.getElementsByName("MealType")[0].value = mealType//Should probably santize this later
        })
    });

    removeFoodItem.forEach(button => {
         button.addEventListener("click", (event) => {
            // console.log("TEST");
            // console.log(event.target);
           nutritionId = button.id
           console.log(nutritionId)
        //    window.location.assign("/calorieTracking?RemoveID=9999");
           fetch(`/calorieTracking?RemoveID=${nutritionId}`, {
            // method: "POST"
           });

        })
    });
})

