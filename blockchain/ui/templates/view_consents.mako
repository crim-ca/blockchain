<html lang="en">
    <%include file="header.mako"/>
    <body>
        <div class="consents">
            <div class="consents-updated">
                Updated: ${updated}
            </div>
            <div class="consents-latest">
                <table>
                    <thead>
                        <tr>
                        %for field in ["Permission", "Consent", "Created", "Expire"]:
                            <th>${field}</th>
                        %endfor
                        </tr>
                    </thead>
                    <tbody>
                    %for consent in consents:
                        <tr>
                        %for field in ["action", "consent", "created", "expire"]:
                            <td>${consent[field]}</td>
                        %endfor
                        </tr>
                    %endfor
                    </tbody>
                </table>
            </div>
            <div class="consents-history">
                <table>
                    <thead>
                        <tr>
                            <th>Changes</th>
                        </tr>
                    </thead>
                    <tbody>
                        %for change in changes:
                        <tr>
                            <td>${change}</td>
                        </tr>
                        %endfor
                    </tbody>
                </table>
            </div>
        </div>
    </body>
</html>
