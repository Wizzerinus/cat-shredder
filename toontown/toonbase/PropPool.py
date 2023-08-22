from direct.actor import Actor
from direct.particles.ParticleEffect import ParticleEffect
from panda3d.core import ConfigVariableInt, Filename

Props = (
    # Battle effects
    (3.5, "stun", "stun-mod", "stun-chan"),
    (3.5, "glow", "glow"),
    (3.5, "suit_explosion_dust", "dust_cloud"),
)


class PropPool:
    """
    The PropPool loads props and their animations if they have them.
    """

    notify = directNotify.newCategory("PropPool")

    def __init__(self):
        self.props = {}
        self.propCache = []
        self.propStrings = {}
        self.propTypes = {}
        self.maxPoolSize = ConfigVariableInt("prop-pool-size", 8).getValue()

        for p in Props:
            phase = p[0]
            propName = p[1]
            modelName = p[2]
            if len(p) == 4:
                animName = p[3]
                propPath = self.getPath(phase, modelName)
                animPath = self.getPath(phase, animName)
                self.propTypes[propName] = "actor"
                self.propStrings[propName] = (propPath, animPath)
            else:
                propPath = self.getPath(phase, modelName)
                self.propTypes[propName] = "model"
                self.propStrings[propName] = (propPath,)

    @staticmethod
    def getPath(phase, model):
        return f"phase_{phase}/models/props/{model}"

    def unloadProps(self):
        """unloadProps()"""
        for p in list(self.props.values()):
            if not isinstance(p, type(())):
                self.__delProp(p)
        self.props = {}
        self.propCache = []

    def getProp(self, name):
        """getProp(name)"""
        assert name in self.propStrings, f"unknown prop name: {name}"
        return self.__getPropCopy(name)

    def __getPropCopy(self, name):
        assert name in self.propStrings
        assert name in self.propTypes
        if self.propTypes[name] == "actor":
            if name not in self.props:
                prop = Actor.Actor()
                prop.loadModel(self.propStrings[name][0])
                animDict = {name: self.propStrings[name][1]}
                prop.loadAnims(animDict)
                prop.setName(name)
                prop.setBlend()
                self.storeProp(name, prop)
            outProp = Actor.Actor(other=self.props[name])
            outProp.setBlend()
            return outProp

        if name not in self.props:
            prop = loader.loadModel(self.propStrings[name][0])
            prop.setName(name)
            self.storeProp(name, prop)
        return self.props[name].copyTo(hidden)

    def storeProp(self, name, prop):
        """storeProp(self, string, nodePath)
        Determine how to store the prop in the prop cache.
        """
        self.props[name] = prop
        self.propCache.append(prop)
        if len(self.props) > self.maxPoolSize:
            oldest = self.propCache.pop(0)
            del self.props[oldest.getName()]
            self.__delProp(oldest)

        self.notify.debug(f"props = {self.props}")
        self.notify.debug(f"propCache = {self.propCache}")

    def getPropType(self, name):
        assert name in self.propTypes
        return self.propTypes[name]

    def __delProp(self, prop):
        """__delProp(self, prop)
        This is a convenience function for deleting prop INSTANCES.
        It does NOT affect the prop dict or cache! Suckah!
        """
        if prop is None:
            self.notify.warning("tried to delete null prop!")
            return
        if isinstance(prop, Actor.Actor):
            prop.cleanup()
        else:
            prop.removeNode()


def createParticleEffect(name, numParticles=None):
    file = Filename(f"phase_3.5/etc/particles/{name}.ptf")
    effect = ParticleEffect()
    effect.loadConfig(file)
    if effect and numParticles is not None:
        particles = effect.getParticlesNamed("particles-1")
        particles.setPoolSize(numParticles)

    return effect


globalPropPool = PropPool()
