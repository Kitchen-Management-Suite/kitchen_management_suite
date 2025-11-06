# Social Contract

## Standup Times
- We agree to meet weekly on Mondays at 5:00 PM EST.

## Meeting Time Restrictions
- Meetings will last no longer than one hour unless absolutely necessary.

## Meeting Locations
- We agree to meet in any available room in Hancock or online if needed.

## Communication Response Times
- We agree to respond to team communications within 24 hours.

## Communication Methods
- Discord will be our primary communication platform.

## Participation
- Everyone is expected to participate equally in meetings and project work.

## Preparation
- We should all look at the weekly requirements and come to class prepared with all requirements for the day.

## Documentation
- Code should be readable, consistent, and well commented.  
- All Flask routes must be documented in a master file.  
- All files should include a header comment block with file path, author(s), inputs/outputs, and general purpose:  

    ```python
    """
    File: <filename>
    File-Path: <filepath>
    Author: <name>
    Date-Created: MM-DD-YYYY

    Description:
        <Brief description of what the script does>

    Inputs:
        <External sources this script uses (ex: files, database, APIs)>

    Outputs:
        <External results this script produces (ex: files, database updates, API responses, logs)>
    """
    # script
    ```

- All functions should be commented with a header block.

    ```python
    def function_name(param1: type, param2: type) -> return_type:
        """
        <Brief description of what the function does>

        Args:
            param1 (type): Description of the first parameter.
            param2 (type): Description of the second parameter.

        Returns:
            return_type: Description of return value.

        Raises:
            ErrorType: Description of the error raised, if applicable.
        """
        # function body
    ```

- All classes should be commented with a header block.

    ```python
    class ClassName:
        """
        <Brief description of what the class represents or does>

        Attributes:
            attr1 (type): Description of attribute 1.
            attr2 (type): Description of attribute 2.

        Methods:
            method_name(param): Description of what the method does
        """

        def __init__(self, attr1, attr2):
            """
            Initialize the ExampleClass with attributes.

            Args:
                attr1 (type): Description of attribute 1.
                attr2 (type): Description of attribute 2.
            """
            self.attr1 = attr1
            self.attr2 = attr2
    ```

## Etiquette
- Be respectful.  
- Be on time.  
- Everyone’s ideas are valuable.  
- When pushing to the repository, always push to a new branch.

## Keeping Wall of Work / Assignments Updated
- The Wall of Work/Assignments board must be updated at least before each class or meeting.

## Late Work
- Work should not be submitted late.  
- If work must be submitted lat, it must still meet the same standards as though it is being graded.
