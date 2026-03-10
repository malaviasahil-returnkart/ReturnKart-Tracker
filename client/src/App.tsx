import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Layout from "@/components/layout";
import Dashboard from "@/pages/dashboard";
import ReturnsList from "@/pages/returns-list";
import ReturnDetail from "@/pages/return-detail";
import NewReturn from "@/pages/new-return";
import TrackReturn from "@/pages/track-return";
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/returns/new" component={NewReturn} />
        <Route path="/returns/:id" component={ReturnDetail} />
        <Route path="/returns" component={ReturnsList} />
        <Route path="/track" component={TrackReturn} />
        <Route component={NotFound} />
      </Switch>
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
