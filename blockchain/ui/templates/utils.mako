<%def name="get_styled_value(value, field)">
    %if value == "None" or value is None or str(value).lower() == "undefined":
        <span class="undefined">undefined</span>
    %elif field in styles:
        %if any(style in styles[field] for style in ["date", "datetime"]):
            <time datetime="${value}" class="${styles[field]}">${value}</span>
        %else:
            <span class="${styles[field]}">${value}</span>
        %endif
    %else:
        <span>${value}</span>
    %endif
</%def>
