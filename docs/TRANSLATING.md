## Préliminaire

Il vous faut un [compte Transifex](https://www.transifex.com/signup/?join_project=prologin-site) puis demander à rejoindre le projet de traduction (vous serez alors `TRANSLATOR`).

## Mode d'emploi : j'aide à traduire

Lorsque les développeurs (MAINTAINERS) du site créent de nouveaux textes, ils vont les envoyer sur la plate-forme de traduction (cf. section suivante). Ces nouveaux textes apparaissent ici :

[https://www.transifex.com/projects/p/prologin-site/translate/#fr/django?translated=no](https://www.transifex.com/projects/p/prologin-site/translate/#fr/django?translated=no)

En tant que `TRANSLATOR`, il vous suffit de sélectionner un texte à gauche, au hasard le premier, écrire la traduction au centre puis faire `<TAB>` (ou cliquer sur _Save_) jusqu'à amener le compteur untranslated, ou votre motivation, à zéro.

Conseils :

*   lisez les commentaires (onglet à droite)
*   n'appliquez pas bêtement les suggestions du site
*   utilisez modérément voire pas du tout la traduction automatique
*   en cas de doute, ajoutez un commentaire
*   en cas de litige, ajoutez un commentaire et marquez-le problématique
*   utilisez Transifex en anglais

### Les reviewers

Il faudrait quelques personnes particulièrement pointilleuses (mot poli pour chiantes), genre `spider-mario`-chiantes, pour effectuer la relecture et les tamponner d'un _seal of approval_. Les traductions approuvées par les `REVIEWERS` ne peuvent pas être changées par les `TRANSLATORS`. Volontaires, levez la main. Pas tous à la fois.

## Mode d'emploi : je développe le site

En développant le site, vous allez naturellement créer de nouveaux textes qu'il faut pousser sur Transifex. Vous voudrez également récupérer les traductions pour tester.

### Préliminaires

1.  Vous devez tout d'abord demander à un `MANAGER` (Zopieux) l'accès `MAINTAINER` sur Transifex afin d'avoir le droit d'update les fichiers sources.
2.  Créez `~/.transifexrc` contenant :  

        [https://www.transifex.com]
        hostname = https://www.transifex.com
        username = MY_TRANSIFEX_USERNAME_AND_NOT_THE_EMAIL
        password = MY_TRANSIFEX_PASSWORD_IN_PLAIN_TEXT
        token =

3.  Arrêtez de rager parce que vous avez un mot de passe en clair dans votre home, et non y'a [pas d'autre solution](http://docs.transifex.com/client/config#transifexrc).

Une fois cela fait, vu que Zopieux est génial et que vous possédez make(1), la procédure est simple.

### Cas de figure : j'ai ajouté/changé des textes sur Django

Vous avez écrit/modifié des `{% trans "foo" %}` ou des `_("bar")`.

1.  Relisez-vous pour éviter de faire traduire des cochonneries par les autres, c'est du temps perdu.
2.  Dans la racine de prologin-site :  

        $ make tx-push

### Cas de figure : les traductions ont avancé, je les veux en local

1.  Dans la racine de prologin-site :  

        $ make tx-pull