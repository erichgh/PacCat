"""
    Formularios utilizados a lo largo de la aplicación de PACCAT.
        - Game
        - Move
        - Counter

    Author
    -------
        Andrés Mena
        Eric Morales
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class SignupForm(forms.ModelForm):
    """
        Formulario para realizar el registro de un usuario

        Attributes
        ----------
        username : CharField
        password : CharField
        password2 : CharField

        Methods
        -------
        clean(self)
            Llama a la función superior y comprueba si hay errores
    """

    username = forms.CharField(max_length=128)
    password = forms.CharField(max_length=128, widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=128, widget=forms.PasswordInput)

    class Meta:
        # Como se relaciona el model con la base de datos
        model = User
        fields = ('username', 'password')

    # Funcion usada para validar un formulario
    def clean(self):
        """
            Llama a la función superior y comprueba si hay errores.

            Parameters
            ----------
            none

            Returns
            -------
            string : errores en caso de haberlos

            Author
            -------
                Andrés Mena
        """

        super(SignupForm, self).clean()
        # extract the username and text field from the data
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        # Comprobamos la logitud del username
        if len(username) < 6:
            self._errors['username'] = self.error_class([
                'Username is too short. It needs at least 6 characters.'])

        # Validamos la contraseña utilizando los validators definidos
        # en settings.py AUTH_PASSWORD_VALIDATORS
        try:
            validate_password(password, username)
        except ValidationError as e:
            self._errors['password'] = e

        # Comprobamos que las contraseñas coinciden
        if password != password2:
            self._errors['password2'] = self.error_class([
                'Password and Repeat password are not the same'])

        # Devolver los errores en caso de haberlos
        return self.cleaned_data


class UserForm(forms.ModelForm):
    """
        Formulario para iniciar sesión.

        Attributes
        ----------
        username : CharField
        password : CharField

        Methods
        -------
        clean_form(self)
            Función para llamar al clean del campo password.
    """

    username = forms.CharField(max_length=32, required=True)
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'password')

    def clear_form(self):
        """
            Función para llamar al clean del campo password.

            Parameters
            ----------
                none

            Returns
            -------
                none

            Author
            -------
                Andrés Mena
        """
        self.password.clean()
