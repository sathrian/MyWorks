#include<linux/kernel.h>
#include<linux/module.h>
#include<linux/netfilter.h>
#include<linux/netfilter_ipv4.h>
#include<linux/ip.h>
#include <linux/moduleparam.h>  

static int running = 0;
static int count = 0 ;
module_param(count, int, 0644);
MODULE_PARM_DESC(count, "drop 1 packet in this many packets");
//char arr[4]={1,1,1,239};
char arr[4]={9,1,1,226};
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Paramaguru");
MODULE_DESCRIPTION("Multicast drop netfilter module");
struct nf_hook_ops in;
unsigned int main_hook(void *priv,struct sk_buff *skb,const struct nf_hook_state *state)
{
	struct sk_buff *pak=NULL;
	pak=skb;
	if(pak) {
		struct iphdr *iph;
		iph = ip_hdr(skb);
		u_int32_t dip=ntohl(iph->daddr);
		if(count>0) {
			//if(((dip&0xe0000000)==0xe0000000) && (!((dip&0xffffffff)==0xffffffff))) {
			if(dip==*(int *)arr) {
				if(running > count) {
					running=0;
					return NF_DROP;
				}
				else
					running++;
			}
		}
	}
	return NF_ACCEPT;
}


static int __init rp_start(void)
{
	in.hook=main_hook;
	in.pf=PF_INET;
	in.hooknum=0; //NF_IP_PRE_ROUTING
	in.priority=NF_IP_PRI_FIRST;
	printk("nf_1 mod installed\n");
	nf_register_hook(&in);
	return 0;
}

static void __exit rp_exit(void)
{
	printk("nf_1 mod exit\n");
	nf_unregister_hook(&in);
}

module_init(rp_start);
module_exit(rp_exit);

