// example_code/unformatted.js

// This is an example of unformatted JavaScript code.
// The formatter plugin should automatically format this file
// after it's been edited by Claude.

function myUnformattedFunction  (  arg1  , arg2 ) {
  if (arg1> arg2)   {
    console.log("arg1 is greater than arg2");
  }else{
    console.log(  "arg2 is greater than or equal to arg1");
  }
  return {
    result: arg1 + arg2
  };
}

// TODO: Add more complex logic here to test the formatter.
const myVariable= "someValue";


// Export the function (or any other parts) to make it a module
module.exports = {
  myUnformattedFunction,
  myVariable
};