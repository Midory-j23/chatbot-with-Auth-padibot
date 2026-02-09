import { MessageSquare, Zap, Shield, Sparkles } from "lucide-react";

const WelcomeState = () => {
  const features = [
    {
      icon: <Zap className="w-5 h-5" />,
      title: "Lightning Fast",
      description: "Get instant responses to your questions",
    },
    {
      icon: <Shield className="w-5 h-5" />,
      title: "Secure & Private",
      description: "Your conversations are protected",
    },
    {
      icon: <Sparkles className="w-5 h-5" />,
      title: "AI Powered",
      description: "Advanced language understanding",
    },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 message-fade-in">
      <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/20 to-accent/10 flex items-center justify-center mb-6 glow animate-pulse-glow">
        <MessageSquare className="w-10 h-10 text-primary" />
      </div>
      
      <h1 className="text-3xl font-bold mb-2">
        <span className="text-gradient">Hello!</span>
        <span className="text-foreground ml-2">How can I help?</span>
      </h1>
      
      <p className="text-muted-foreground text-center max-w-md mb-10">
        I'm your AI assistant. Ask me anything and I'll do my best to help you out.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl w-full">
        {features.map((feature, index) => (
          <div
            key={index}
            className="glass rounded-xl p-4 text-center hover:border-primary/50 transition-colors duration-300"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mx-auto mb-3 text-primary">
              {feature.icon}
            </div>
            <h3 className="font-medium text-sm mb-1">{feature.title}</h3>
            <p className="text-xs text-muted-foreground">{feature.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WelcomeState;
