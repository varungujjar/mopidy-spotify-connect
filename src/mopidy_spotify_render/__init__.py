import pathlib
from mopidy import config, ext

class Extension(ext.Extension):
    dist_name = "Mopidy-Spotify-Render"
    ext_name = "spotify-render"
    version = "0.1.0"

    def get_default_config(self):
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()

        schema["name"] = config.String()
        schema["bitrate"] = config.String()
        schema["format"] = config.String()
        schema["initial-volume"] = config.String()
        schema["backend"] = config.String()
        schema["device-type"] = config.String()
        schema["device"] = config.String()
        schema["autoplay"] = config.Boolean()
        schema["passthrough"] = config.Boolean()
        schema["onevent"] = config.String()
        schema["emit-sink-events"] = config.Boolean()
        return schema


    def setup(self, registry):
        from .frontend import SpotifyRenderFrontend
        registry.add("frontend", SpotifyRenderFrontend)
