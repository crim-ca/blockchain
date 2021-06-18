<html lang="en">
    <%include file="header.mako"/>
    <body>
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
                            <td>${link['name']}</td>
                            <td><a href="${link['href']}">${link['href']}</a></td>
                        </tr>
                    %endfor
                </tbody>
            </table>
        </div>
    </body>
</html>
