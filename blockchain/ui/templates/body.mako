<%doc>
    Base template for every other page that should provide relevant body contents.
</%doc>
<html lang="en">
    <%include file="header.mako"/>
    <body>
    ${self.body()}
    </body>
    <%include file="version.mako"/>
</html>
