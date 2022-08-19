# Understanding checks for green sites

It's worth referring to the general principle we apply when checking if a site or a services from a digital provider is green:

> If you want a green site, you need to demonstrate steps you are taking to avoid, reduce or offset the greenhouse gas emissions caused using electricity to provide the service. You need to do this on a yearly basis, or better.

The two main ways we track this being done are either running a service powered by green energy, or using a service from a provider using green energy. You can [read more about what we class as green energy and what evidence we required on our main site][1] - this content explains how we establish the link between a site and the supporting evidence linked to a given service.

[1]: https://www.thegreenwebfoundation.org/what-we-accept-as-evidence-of-green-power/

## Making this more specific

More concretely, when we do a check for a site, we are usually looking up a domain like mycoolsite.com, then resolving that to an IP address. Once we have the IP address, we check it against a set of IP ranges or Autonomous System networks (ASN) that are associated with a given provider that we have supporting evidence for. We outline each approach below.

Once we the IP address, we take one of three paths to arrive at an organisation that we have information for.

1. Domain, to IP to provider, by IP range
2. Domain to IP to provider, by ASN
3. Domain to carbon.txt lookup, to provider(s)

We'll cover each one in turn.

### Domain, to IP to provider, by IP range

Once we have an IP address, we establish the link a provider by checking if this IP falls insite a one of the IP ranges already shared with us by a given service provider.

#### Linking directly to a provider by IP range

So, if an IP address is 123.123.123.100, and we have an IP range for Provider A, who has registered the IP range 123.123.123.1 to 123.123.123.255, we associate the lookup with that provider, and refer to the supporting evidence shared with us by Provider A.

This is the simplest case - where a domain might be `provider-a.com`, resolving to the IP address, which we then link to Provider A, the organisation.

#### Linking a site to a provider in the site's supply chain

There will be cases where an organisation isn't running its own servers or other infrastructure itself, but instead of using a service from a green provider. Historically, this has been the most common scenario, because one hosting provider will typically host lots of websites on behalf of other organisations.

In this case a domain might be `my-cool-site.com`, which resolving to the IP address, which we then link to Provider A, the organisation.


### Domain, to IP to provider, by ASN

For some larger providers, maintaining a register of every single IP Range with the green web foundation can be cumbersome, so we also support lookups by Autonomous System Network (ASN) instead.

There are millions of IP addresses in the world, but the internet is a big place, and they are not infinite. An organisation called the Internet Assigned Numbers Authority, IANA allocates these blocks of IP ranges to _regional internet registries_, who then allocate them either to organisations for use directly, or to smaller, _local internet registries_ who then allocate them to organisations like _internet service providers_, (ISPs) or companies using them directly themselves.

Maintaining which individual IP address points to which is something that is often better managed at the local level, and the internet itself made of up tens of thousands smaller networks called Autonomous Systems Networks, that manage this themselves.

If we don't have a matching range for an IP address, we can perform a lookup to see which AS Network the IP address belongs to - if an entire AS network belongs to one organisation, and we have supporting evidence for the organisation using enough green energy, this saves duplicating the records that the AS network is managing themselves.

As before, we support two cases - an organisation providing a digital service themselves, or an organistion using a green provider to provide a service.

#### Linking directly to a provider by ASN

In this case, a domain might be `provider-b.com`, resolving to the IP address `231.231.231.231`. From there we perform a lookup to find Autonomous Network 12345 (`AS 12345`), which is owned exclusively by `Provider B`, the organisation, and has been registered with us.

By following the link to supporting evidence shared by `Provider B`, we can establish the link to green energy.

#### Linking a site to a provider in the site's supply chain

Similarly, a domain `my-green-site.com`, which resolves to the IP address `213.213.212.213`. From there, we perform a lookup to the same Autonomous Network 12345 (`AS 12345`). We folow the link from `AS 12345 to link to Provider B, and refer to their evidence to establish the link to green energy.

------

### Domain to carbon.txt lookup

The final supported approach, which is currently under development, is to avoid relying on IP addresses entirely, and go straight from a domain name, to one or more providers, based on machine readable information exposed in a `carbon.txt` file.

Here we follow a link from the domain name to a `carbon.txt` file at one of a few well known locations, somewhat like `robots.txt` works, or how some DNS TXT record lookups work. We then parse the `carbon.txt` file to follow the links to the necessary providers.

For more, please follow the link to the [github repo where the syntax and conventions are being worked at out](https://github.com/thegreenwebfoundation/carbon.txt).
