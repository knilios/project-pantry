from webpage.models import Recipe, Equipment, Ingredient, RecipeStep, IngredientList, EquipmentList, Diet
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from abc import ABC, abstractmethod
import requests
from decouple import config

API_KEY = config('API_KEY', default='fake-secret-key')
spoonacular_password = config('SPOONACULAR_PASSWORD')

class Builder(ABC):
    """
    Abstract base class for constructing recipe objects.

    This class defines the interface for building various components of a recipe,
    including the recipe itself, its ingredients, required equipment, and steps.
    Concrete implementations must provide specific logic for each method.
    """

    @abstractmethod
    def build_recipe(self) -> Recipe:
        """
        Build and return the main recipe object.

        :return: A Recipe object that represents the constructed recipe.
        """
        pass
    
    @abstractmethod
    def build_details(self):
        """
        Build the properties of the recipe.
        """
        pass

    @abstractmethod
    def build_ingredient(self, ingredient: Ingredient, amount: int, unit: str):
        """
        Build the ingredients associated with the recipe.

        :param ingredient: The ingredient used in the recipe.
        :param amount: The amount of the ingredient needed in the recipe.
        :param unit: The unit of the ingredient amount eg. Grams, Kg.
        """
        pass

    @abstractmethod
    def build_equipment(self, equipment: Equipment, amount: int, unit: str):
        """
        Build the equipment needed for the recipe.

        :param equipment: The equipment used in the recipe.
        :param amount: The amount of the equipment needed in the recipe.
        :param unit: The unit of the equipment amount eg. Grams, spoon.
        """
        pass

    @abstractmethod
    def build_step(self, step: RecipeStep):
        """
        Build the step in the recipe.

        :param step: The step in the recipe.
        """
        pass

    @abstractmethod
    def build_user(self, user: User):
        """
        Build the user which is the author of the recipe.

        :param user: The user that is the author of the recipe.
        """
        pass
    
    @abstractmethod
    def build_spoonacular_id(self, spoonacular_id:int):
        """
        Build the spoonacular_id property of the Recipe class.
        
        :param spoonacular_id: The Spoonacular ID of the Recipe.
        """
        pass


class NormalRecipeBuilder(Builder):
    """
    Concrete implementation of Builder for constructing recipes in normal cases.

    This class is responsible for assembling a Recipe object along with its
    associated ingredients and equipment using information from the user.
    """

    def __init__(self, name: str, user: User):
        """
        Initialize the NormalRecipeBuilder instance.

        :param name: The name of the recipe.
        :param user: The user that is the author of the recipe.
        """
        self.__recipe = Recipe.objects.create(name=name, poster_id=user)
        
    def build_details(self, **kwargs): # Bad code change later.
        """Build the properties of the Recipe class"""
        # Process keyword arguments
        for key, value in kwargs.items():
            setattr(self.__recipe, key, value)

    def build_recipe(self) -> Recipe:
        """
        Build and return a standard Recipe object.

        :return: A Recipe object that represents the constructed standard recipe.
        """
        return self.__recipe

    def build_ingredient(self, ingredient: Ingredient, amount: int, unit: str):
        """
        Build and return the ingredients for the standard recipe.

        :param ingredient: The ingredient used in the recipe.
        :param amount: The amount of the ingredient needed in the recipe.
        :param unit: The unit of the ingredient amount eg. Grams, Kg.
        """
        ingredient_list = IngredientList(
            recipe = self.__recipe,
            ingredient  = ingredient,
            amount = amount,
            unit = unit
        )
        ingredient_list.save()
    
    def build_equipment(self, equipment: Equipment, amount: int=1, unit: str="thing"):
        """
        Build the equipment needed for the standard recipe.

        :param equipment: The equipment used in the recipe.
        :param amount: The amount of the equipment needed in the recipe.
        :param unit: The unit of the equipment amount eg. Grams, spoon.
        """
        equipment_list = EquipmentList.objects.create(
            recipe = self.__recipe,
            equipment = equipment,
            amount = amount,
            unit = unit
        )
        equipment_list.save()
    
    def build_step(self, step_description: str):
        """
        Build the step in the standard recipe.

        :param step_description: The description of the step you are adding.
        """
        number = 0
        try:
            post_last_step = RecipeStep.objects.filter(recipe = self.__recipe).order_by('-number').first()
            if post_last_step is None:
                number += 1
            else:
                number = post_last_step.number + 1
        except ObjectDoesNotExist:
            number += 1
        step = RecipeStep.objects.create(description=step_description, recipe=self.__recipe)
        step.number = number
        step.save()
    
    def build_user(self, user: User):
        """
        Build the user which is the author of the recipe.

        :param user: The user that is the author of the recipe.
        """
        self.__recipe.poster_id = user
        self.__recipe.save()
        
    def build_spoonacular_id(self, spoonacular_id:int):
        self.__recipe.spoonacular_id = spoonacular_id
        self.__recipe.save()


class SpoonacularRecipeBuilder(Builder):
    """
    This class is unused, for now.
    
    Concrete implementation of Builder for constructing recipes from Spoonacular API data.

    This class is responsible for assembling a Recipe object along with its
    associated ingredients and equipment using data retrieved from the Spoonacular API.
    """

    def __init__(self, name: str, spoonacular_id: str):
        """
        Initialize the SpoonacularRecipeBuilder instance.

        :param name: The name of the recipe.
        :param spoonacular_id: The id of the Recipe in the Spoonacular database.
        """
        self.__url = f'https://api.spoonacular.com/recipes/{spoonacular_id}/information'
        self.__equipment_url = f'https://api.spoonacular.com/recipes/{spoonacular_id}/equipmentWidget.json'
        self.spoonacular_id = spoonacular_id
        self.name = name
        self.__api_is_called = False
        self.__api_equipment_is_fetch = False
        
        self.__builder = NormalRecipeBuilder(name=self.name, user=self.__create_spoonacular_user()) # This needs fixing later
        
    def __create_spoonacular_user(self) -> User: # Fix later
        """
        Create a spoonacular user in the local database.
        
        :return: A spoonacular user class.
        """
        # Create a test user
        user = User.objects.filter(username = "Spoonacular").first()
        if(user is None):
            user = User(username = "Spoonacular", password=spoonacular_password)
            user.save()
        return user
        
    def __call_api(self):
        """Fetch the information about the recipe from the Spoonacular API"""
        if(not self.__api_is_called):
            response = requests.get(self.__url, params={'apiKey': API_KEY})
            
            if response.status_code == 200:
                self.__data = response.json()
                self.__api_is_called = True
            else:
                raise Exception("Cannot load the recipe")
            
    def __fetch_equipment(self):
        """
        Fetch the equipments of the recipe from the Spoonacular API.
        Raise an Exeption if the recipe cannot be found.
        """
        if(not self.__api_equipment_is_fetch):
            response = requests.get(self.__equipment_url, params={'apiKey': API_KEY})
            
            if response.status_code == 200:
                self.__equipement_data = response.json()
                self.__api_equipment_is_fetch = True
            else:
                raise Exception("Cannot load the recipe")
            
    def build_details(self):
        """
        Build the image and estimated_time properties of the recipe.
        Raise an Exeption if the recipe cannot be found.
        """
        self.__call_api()
        self.__builder.build_details(image=self.__data["image"])
        self.__builder.build_details(estimated_time=self.__data["readyInMinutes"])
        self.__builder.build_details(description=self.__data["summary"])

    def build_name(self):
        """
        Build the name of the recipe, if you have not already add it in the initialize.
        Raise an Exeption if the recipe cannot be found.
        """
        self.__call_api()
        self.__builder.build_details(name=self.__data["title"])

    def build_recipe(self) -> Recipe:
        """
        Return a Recipe object with data from Spoonacular API.
        Raise an Exeption if the recipe cannot be found.

        :return: A Recipe object that represents the constructed recipe based on
        Spoonacular data.
        """
        return self.__builder.build_recipe()

    def build_ingredient(self):
        """
        Build the ingredients for the recipe sourced from Spoonacular API.
        Raise an Exeption if the recipe cannot be found.
        """
        self.__call_api()
                
        # Use builder
        for ingredient_data in self.__data.get('extendedIngredients', []):
            ingredient, _ = Ingredient.objects.get_or_create(
                spoonacular_id=ingredient_data['id'],
                defaults={'name': ingredient_data['name'],
                          'picture': ingredient_data['image'],}
            )
            ingredient.save()
            self.__builder.build_ingredient(
                ingredient=ingredient,
                amount=ingredient_data['measures']['metric']['amount'],
                unit=ingredient_data['measures']['metric']['unitLong'],
                )

    def build_step(self):
        """
        Build the step in the Spoonacular recipe.
        Raise an Exeption if the recipe cannot be found.
        """
        self.__call_api()
        for instruction in self.__data.get('analyzedInstructions', []):
            for step_data in instruction.get('steps', []):
                self.__builder.build_step(step_data['step'])
        
    def build_equipment(self):
        """
        Build the equipment needed for the recipe sourced from Spoonacular API.
        Raise an Exeption if the recipe cannot be found.
        """
        self.__fetch_equipment()
        
        # Save the equipment (if available)
        for equipment_data in self.__equipement_data.get('equipment', []):
            equipment, _ = Equipment.objects.get_or_create(
                name = equipment_data['name'],
                picture = equipment_data['image']
            )
            equipment.save()
            self.__builder.build_equipment(
                equipment=equipment,

                )

    def build_diet(self):
        self.__call_api()
        # Diet information from Spoonacular
        diets_from_api = self.__data.get('diets', [])
        for diet_name in diets_from_api:
            diet, _ = Diet.objects.get_or_create(name=diet_name)
            self.__builder.build_details(diets=[diet])

    def build_user(self, user: User): # Bad code to be remove
        """
        Build the user which is the author of the recipe.

        :param user: The user that is the author of the recipe.
        """
        pass
        
    def build_spoonacular_id(self):
        """Build the Spoonacular ID for the Recipe class."""
        self.__call_api()
        self.__builder.build_spoonacular_id(int(self.__data["id"]))
