<html lang="en">
    <%include file="header.mako"/>
    <body>
        <%include file="body_menu.mako"/>
        <div class="shortcut-links">
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
                    %for link in links:
                        <tr>
                            <td>${link['title']}</td>
                            <td><a href="${link['href']}">${link['href']}</a></td>
                        </tr>
                    %endfor
                </tbody>
            </table>
        </div>
    </body>
</html>
