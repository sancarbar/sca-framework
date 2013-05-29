


function validateSignUpForm(formId){
    if(!validInput(1, $('#username').val(), true)){
        $('#control-group-username').addClass('error');
        $('#username_error').html('invalid value');
        return false;
    }else{
        $('#control-group-username').removeClass('error');
        $('#username_error').html('');
    }
    if(!validInput(4, $('#password').val(), true)){
        $('#control-group-password').addClass('error');
        $('#password_error').html('invalid value');
        return false;
    }else{
        $('#control-group-password').removeClass('error');
        $('#password_error').html('');
    }
    if($('#password').val() != $('#verify').val()){
        $('#control-group-verify').addClass('error');
        $('#verify_error').html('passwords did not match');
        return false;
    }else{
        $('#control-group-verify').removeClass('error');
        $('#verify_error').html('');
    }
    if(!validInput(3, $('#email').val(), true)){
        $('#control-group-email').addClass('error');
        $('#email_error').html('invalid value');
        return false;
    }else{
        $('#control-group-email').removeClass('error');
        $('#email_error').html('');
    }
    $('#'+formId).submit();
}


function validInput(inputType, inputValue, noNull){

    //null validation
    if(noNull && inputValue == '')
        return false

    switch(inputType){
        case 1:  //string length
            return inputValue.length <= 45;
        case 2: //numeric value
            return inputValue.match(/^\s*[+-]?\d+\s*$/);
        case 3: //email
            return inputValue.match(/^[a-z][\w.-]+@\w[\w.-]+\.[\w.-]*[a-z][a-z]$/i);
        case 4: //password
            return inputValue.match(/^.{3,20}$/);
    }
}